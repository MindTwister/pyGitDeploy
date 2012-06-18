import ConfigParser


# ConfigReader
# ======
# GitDeploy compatible ConfigParser
#
# Wraps ConfigParser in an interface that is compatible with the configreader
# found in GitDeploy
class ConfigReader(ConfigParser.RawConfigParser):
    def __init__(self, postfix=""):
        self.postfix = postfix
        ConfigParser.RawConfigParser.__init__(self)
        self.read("deploy.cfg")

    def has_option(self, section, option):
        if self.postfix is not "":
            section = section + ":" + self.postfix
        return ConfigParser.RawConfigParser.has_option(self, section, option)

    # `get_value` is itself simply a wrapper around `get`
    def get_value(self, section, option):
        if self.postfix is not "":
            section = section + ":" + self.postfix
        return self.get(section, option)


# ConfigWriter
# ======
# GitDeploy compatible ConfigParser
#
# Wraps ConfigParser in an interface that is compatible with the configwriter
# found in GitDeploy
class ConfigWriter(ConfigParser.RawConfigParser):
    def __init__(self, postfix=""):
        self.postfix = postfix
        ConfigParser.RawConfigParser.__init__(self)
        self.read("deploy.cfg")

    def set_value(self, section, option, value):
        if self.postfix is not "":
            section = section + ":" + self.postfix
        # Set value expects a section to be created if it does not already
        # exist
        if not self.has_section(section):
            self.add_section(section)
        self.set(section, option, value)
        with open("deploy.cfg", "wb") as configfile:
            self.write(configfile)
