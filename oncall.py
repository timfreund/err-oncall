from errbot.botplugin import BotPlugin
from errbot import botcmd
from twilio.rest import TwilioRestClient
import logging

log = logging.getLogger('errbot.botplugin.OnCall')

class OnCall(BotPlugin):
    def activate(self):
        BotPlugin.activate(self)
        self.twilio_config_available = True
        self.twilio = None
        if 'config' not in self:
            log.info("Shelf is missing config, creating new config dictionary")
            self['config'] = {'twilio.account_sid': None,
                              'twilio.auth_token': None,
                              'twilio.default_sender': None}
        else:
            log.info("Shelf contains config")
            log.info(self['config'])

        if 'users' not in self:
            self['users'] = {}

        self.validate_twilio_config()
        if self.twilio_config_available:
            self.configure_twilio()

    def configure_twilio(self):
        self.account_sid = self['config']['twilio.account_sid']
        self.auth_token = self['config']['twilio.auth_token']
        self.twilio = TwilioRestClient(self.account_sid, self.auth_token)

    def validate_twilio_config(self):
        self.twilio_config_available = True
        for key in ['twilio.account_sid', 'twilio.auth_token', 'twilio.default_sender']:
            if self['config'][key] is None:
                self.send("", "Missing configuration value for %s" % key)
                self.twilio_config_available = False

    def delete_user(self, username):
        users = self['users']
        del users[username]
        self['users'] = users

    def set_user(self, username, phone_number):
        users = self['users']
        users[username] = {'phone_number': phone_number}
        self['users'] = users

    @botcmd
    def oncall_config_set(self, message, args):
        """Set On Call configuration values: oncall config_set KEY VALUE"""
        key, value = args.split(" ", 1)
        c = self['config']
        c[key] = value
        self['config'] = c
        self.validate_twilio_config()
        if self.twilio_config_available:
            self.configure_twilio()

        return ("Set %s to %s" % (key, value))

    @botcmd
    def oncall_define_user(self, message, args):
        """Create a user in the OnCall Directory: NAME, PHONE_NUMBER"""
        username, phone_number = [x.strip() for x in args.split(',', 1)]
        if phone_number.find("+1") == -1:
            yield("Adding the +1 country code to %s" % phone_number)
            phone_number = "+1%s" % phone_number.replace("-", "")
        self.set_user(username, phone_number)
        yield("%s was created" % username)

    @botcmd
    def oncall_delete_user(self, message, args):
        """Delete a user from the OnCall directory"""
        if args in self['users']:
            users = self['users']
            del users[args]
            self['users'] = users
            return("Deleted %s" % args)
        else:
            return("%s not found in the users list" % args)

    @botcmd
    def oncall_list_users(self, message, args):
        """ List all users with phone numbers defined in the OnCall directory"""
        for k, v in self['users'].items():
            yield("%s" % k)

    @botcmd 
    def sms(self, message, args):
        """SMS a known user"""
        to  = args.strip()
        if to in self['users']:
            user = self['users'][to]
            self.twilio.sms.messages.create(to=user['phone_number'], from_=self['config']['twilio.default_sender'],
                                            body="Your assistance is requested in the group chat.")
            return("%s has been summoned." % to)
        else:
            return("Unknown user: %s" % to)


    
