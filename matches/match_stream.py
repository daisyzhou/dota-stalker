import collections
import http.client
import json
import logging
import socket
import time

from matches import util
import local_config


class MatchStream:
    """
    Gets matches from the Dota 2 web API
    (see http://dev.dota2.com/showthread.php?t=58317 and
    https://wiki.teamfortress.com/wiki/WebAPI#Dota_2) and provides an iterator interface to them.
    Matches can only be iterated through once.

    This class is not thread-safe.
    """

    def __init__(self):
        self.running = False
        # Internal storage of matches that haven't been iterated through yet
        self._matches = collections.deque()
        self._poll_seconds = None
        self._most_recent_streamed_match = None
        self._connection = None
        self._last_poll_time = None

    def start(self, poll_seconds=1):
        """
        Starts the Streamer; may not be started if it is already running.
        :param poll_seconds: Number of seconds after which to poll for new
          matches.  Default is 1.  Valve suggests rate limiting within
          applications to at most one request per second.
        """
        self.running = True
        self._connection = util.create_steamapi_connection()
        self._poll_seconds = float(poll_seconds)
        self._last_poll_time = time.time()
        self._most_recent_streamed_match = self._get_recent_match_seq_num()

    def stop(self):
        """
        Stops the Streamer.  Closes all connections.
        :return:
        """
        self.running = False
        self._connection.close()

    def _reconnect_connection(self, num_attempts=0):
        """
        Reconnect the steam API connection, because sometimes it fails...
        Retries up to 'num_attempts' times, waiting for self.poll_interval in
        between each retry.  'num_attempts' of -1 signifies to retry forever.

        Raises the socket.timeout if it times out for num_attempts times.

        :param num_attempts: Number of times to attempt to retry.  Default 10.
        """
        try:
            self._connection.close()
            time.sleep(self._poll_seconds)
            self._connection.connect()
        # Except all exceptions... I don't have time for this
        except (socket.timeout, ConnectionRefusedError, Exception) as e:
            if num_attempts == -1:
                logging.warning("Reconnect failed, retrying forever.")
                self._reconnect_connection(num_attempts=-1)
            elif num_attempts > 1:
                logging.warning("Reconnect failed, retrying %d more times" %
                                (num_attempts - 1))
                self._reconnect_connection(num_attempts - 1)
            else:
                logging.error("Reconnect failed.")
                raise e

    def _get_recent_match_seq_num(self):
        """
        :return: A match_seq_num of a recent match to start streaming from.
        """
        self._connection.request(
            "GET",
            "/IDOTA2Match_570/GetMatchHistory/V001/"
            "?key={key}"
            "&matches_requested=1"
                .format(
                key=local_config.DOTA2_API_KEY
            )
        )
        response = self._connection.getresponse()
        decoded = json.loads(response.read().decode("utf-8"))
        time.sleep(self._poll_seconds)  # Rate limit for the API
        return decoded["result"]["matches"][-1]["match_seq_num"]

    def __iter__(self):
        return self

    def __next__(self):
        """
        Return the next match we already have, or get more matches if we're out of existing ones.

        :return: the next match
        """
        if len(self._matches) == 0:
            for match in self._get_next_matches():
                self._matches.append(match)
        return self._matches.popleft()

    def _get_next_matches(self):
        """
        Blocks until there are new matches.

        :return: New matches.
        """
        while True:
            # If it's been < poll_seconds since the last time we tried to get matches, wait poll_seconds.
            if time.time() - self._last_poll_time < self._poll_seconds:
                time.sleep(self._poll_seconds)

            self._last_poll_time = time.time()
            matches = self._maybe_get_next_matches()
            if matches:
                self._most_recent_streamed_match = matches[-1]["match_seq_num"]
                return matches

            time.sleep(self._poll_seconds)

    def _maybe_get_next_matches(self):
        self._connection.request(
            "GET",
            "/IDOTA2Match_570/GetMatchHistoryBySequenceNum/V001/"
            "?key={key}&start_at_match_seq_num={match_seq_num}"
                .format(
                key=local_config.DOTA2_API_KEY,
                match_seq_num=self._most_recent_streamed_match + 1
            )
        )
        try:
            response = self._connection.getresponse().read()
        except http.client.BadStatusLine:
            logging.info("Received empty response (BadStatusLine), "
                         "waiting & continuing...")
            self._reconnect_connection(num_attempts=-1)
            return None
        except socket.timeout:
            logging.info("Connection timed out, "
                         "waiting & continuing...")
            self._reconnect_connection(num_attempts=-1)
            return None
        except ConnectionResetError:
            logging.info("Connection reset, waiting & continuing...")
            self._reconnect_connection(num_attempts=-1)
            return None
        except Exception as e:
            logging.info("Got exception while getting next matches: ", e)
            return None

        try:
            match_history = json.loads(response.decode("utf-8"))
        except ValueError as e:
            logging.error(
                "Error while decoding JSON response: %s. Error:\n%s"
                % (response, e)
            )
            return None
        if "result" not in match_history:
            logging.warning("JSON Malformed result: %s" % match_history)
            return None
        if "matches" not in match_history["result"]:
            # Reached end for now.
            logging.info("No new matches, continuing ...")
            return None

        json_matches = match_history["result"]["matches"]
        if len(json_matches) == 0:
            logging.warning("No matches in 'matches' field of result, this "
                            "is unexpected. json received was:\n%s" %
                            match_history)
            return None

        return json_matches

