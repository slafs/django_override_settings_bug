from django.test import override_settings, SimpleTestCase
from django.core import signals
from django.conf import settings

settings.configure()


class SettingChangeException(Exception):
    pass


class SettingChangeEnterException(Exception):
    pass


class SettingChangeExitException(Exception):
    pass

def change_settings_receiver(*args, **kwargs):
    setting = kwargs['setting']
    enter = kwargs['enter']

    if setting == 'SETTING_B':
        raise SettingChangeException
    if setting == 'SETTING_C' and enter:
        raise SettingChangeEnterException
    if setting == 'SETTING_D' and not enter:
        raise SettingChangeExitException


signals.setting_changed.connect(change_settings_receiver)


class OverrideSettingsTest(SimpleTestCase):

    def test_override_settings_both(self):

        with self.assertRaises(SettingChangeException):
            with override_settings(SETTING_A='X', SETTING_Z='X', SETTING_B='X'):
                pass

        self.assertEquals(settings.SETTING_A, 'A')
        self.assertEquals(settings.SETTING_B, 'B')
        self.assertEquals(settings.SETTING_C, 'C')
        self.assertEquals(settings.SETTING_D, 'D')
        self.assertEquals(settings.SETTING_Z, 'Z')

    def test_override_settings_enter(self):

        with self.assertRaises(SettingChangeEnterException):
            with override_settings(SETTING_A='X', SETTING_Z='X', SETTING_C='X'):
                pass

        self.assertEquals(settings.SETTING_A, 'A')
        self.assertEquals(settings.SETTING_B, 'B')
        self.assertEquals(settings.SETTING_C, 'C')
        self.assertEquals(settings.SETTING_D, 'D')
        self.assertEquals(settings.SETTING_Z, 'Z')

    def test_override_settings_exit(self):

        with self.assertRaises(SettingChangeExitException):
            with override_settings(SETTING_A='X', SETTING_Z='X', SETTING_D='X'):
                pass

        self.assertEquals(settings.SETTING_A, 'A')
        self.assertEquals(settings.SETTING_B, 'B')
        self.assertEquals(settings.SETTING_C, 'C')
        self.assertEquals(settings.SETTING_D, 'D')
        self.assertEquals(settings.SETTING_Z, 'Z')

