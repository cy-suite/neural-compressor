"""Tests for logging utilities."""
import unittest

from neural_compressor.common import Logger, logger

inc_logger = Logger().get_logger()  # `inc_logger` is the same as `logger`

msg_lst = [
    "call logger log function.",
    {"msg": "call logger warning function"},
    ["call logger warning function", "done"],
    ({"msg": "call logger warning function"}, {"msg2": "done"}),
    {"msg": {("bert", "embedding"): {"weight": {"dtype": ["unint8", "int8"]}}}},
    {"msg": [{"sub_msg": "call logger"}, {"sub_msg2": "call warning function"}]},
    {"msg2": "done"},
    {("bert", "embedding"): {"op": ("a", "b")}},
]


class TestLogger(unittest.TestCase):
    def test_logger(self):
        logger.log(0, "call logger log function.")
        logger.log(1, {"msg": "call logger log function."})
        logger.debug("call logger debug function.")
        logger.debug({"msg": "call logger debug function."})
        logger.error("call logger error function.")
        logger.error({"msg": "call logger error function."})
        logger.fatal("call logger fatal function")
        logger.fatal({"msg": "call logger fatal function"})
        logger.info("call logger info function")
        logger.info({"msg": "call logger info function."})
        logger.warning("call logger warning function")
        logger.warning({"msg": "call logger warning function"})
        logger.warning(["call logger warning function", "done"])
        logger.warning(("call logger warning function", "done"))
        logger.warning({"msg": {("bert", "embedding"): {"weight": {"dtype": ["unint8", "int8"]}}}})
        logger.warning({"msg": {("bert", "embedding"): {"op": ("a", "b")}}})
        # the following log will not be prettified
        logger.warning([{"msg": "call logger warning function"}, {"msg2": "done"}])
        logger.warning(({"msg": "call logger warning function"}, {"msg2": "done"}))
        logger.warning(({"msg": [{"sub_msg": "call logger"}, {"sub_msg2": "call warning function"}]}, {"msg2": "done"}))

    def test_in_logger(self):
        inc_logger.log(0, "call logger log function.")
        inc_logger.log(1, {"msg": "call logger log function."})
        inc_logger.debug("call logger debug function.")
        inc_logger.debug({"msg": "call logger debug function."})

    def test_logger_func(self):
        from neural_compressor.common import debug, error, fatal, info, level, log, warning

        for msg in msg_lst:
            log(level=1, msg=msg)
            info(msg=msg)
            debug(msg=msg)
            warning(msg=msg)
            error(msg=msg)
            fatal(msg=msg)


if __name__ == "__main__":
    unittest.main()
