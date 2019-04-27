from birbapi.birbapi import timestr_to_timestamp, Twitter, TwitterError, RequestsError


class TestBirbAPI():
    def test_timestr_to_timestamp(self):
        assert timestr_to_timestamp("Wed Aug 27 13:08:45 +0000 2008") == 1219867725.0
