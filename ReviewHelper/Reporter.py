import time


class Reporter:
    """
        Logs execution details and writes Review file with valuable data
    """

    def __init__(self):
        self.verbose = True
        self.config = None
        self.reviewLogFile = None
        self.msg_prefix = ""
        self.logFile = "log.log"
        self.log("START", "--------------------------------", "w+")

    def setup(self, config):
        self.config = config
        self.reviewLogFile = "Review.log"
        self.write_review("-------- Review started ------", "w+")

    def set_msg_prefix(self, prefix):
        self.msg_prefix = " " + prefix

    def write_review(self, message, mode="a"):
        try:
            with open(self.reviewLogFile, mode) as f:
                f.write(message + "\n")
                f.close()
        except:
            self.fatal("Error happened during log writing!")

    def log(self, msg_type, message, mode="a"):
        try:
            with open(self.logFile, mode) as f:
                msg = "{} [{}]{} {}\n".format(
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    msg_type,
                    self.msg_prefix,
                    message
                )
                print(msg)
                f.write(msg)
                f.close()
        except:
            print("Error happened during log writing!")

    def info(self, message):
        self.log("INFO", message)

    def warn(self, message):
        self.log("WARN", message)

    def error(self, message):
        self.log("ERROR", message)

    def fatal(self, message):
        self.log("FATAL ERROR", message)

    def format_review_msg(self, type, code, arg1="", arg2="", arg3="", arg4=""):
        return "[{}] {}".format(type, self.config.get(type.lower() + str(code)).format(arg1, arg2, arg3, arg4))

    def review_info(self, code, arg1="", arg2="", arg3="", arg4=""):
        if not self.verbose:
            return ()
        self.write_review(self.format_review_msg("INFO", code, arg1, arg2, arg3, arg4))

    def review_warn(self, code, arg1="", arg2="", arg3="", arg4=""):
        self.write_review(self.format_review_msg("WRN", code, arg1, arg2, arg3, arg4))

    def review_error(self, code, arg1="", arg2="", arg3="", arg4=""):
        self.write_review(self.format_review_msg("ERR", code, arg1, arg2, arg3, arg4))
