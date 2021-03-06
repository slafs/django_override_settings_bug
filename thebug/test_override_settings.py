try:
    from unittest import mock
except ImportError:
    import mock

from django.test import override_settings, SimpleTestCase
from django.core import signals
from django.conf import settings

settings.configure(
    SETTING_A='A',
    SETTING_B='B',
    SETTING_C='C',
    SETTING_D='D',
    SETTING_Z='Z',
)


class SettingChangeException(Exception):
    pass


class SettingChangeEnterException(Exception):
    pass


class SettingChangeExitException(Exception):
    pass


def change_settings_receiver(*args, **kwargs):
    """
    A receiver for demonstration purposes.
    It fails while certain settings are being changed.

    SETTING_B raises an error while receiving the signal on both entering and exiting the context manager
    SETTING_C raises an error only on enter.
    SETTING_D raises an error only on exit.
    """
    setting = kwargs['setting']
    enter = kwargs['enter']

    if setting == 'SETTING_B':
        raise SettingChangeException
    if setting == 'SETTING_C' and enter:
        raise SettingChangeEnterException
    if setting == 'SETTING_D' and not enter:
        raise SettingChangeExitException


signals.setting_changed.connect(change_settings_receiver)


def filter_mock_calls(mock_calls, **kwargs):
    """
    From the given mock_calls list return only those calls
    that were done with ``kwargs``.
    """
    for mock_call in mock_calls:
        _, call_args, call_kwargs = mock_call
        if all((k, v) in call_kwargs.items() for k, v in kwargs.items()):
            yield mock_call


class OverrideSettingsTest(SimpleTestCase):
    """
    Test three cases of "setting_changed" signal receiver failure
    while using the override_settings context manager:

    1) receiver fails when the signal is sent while both entering and exiting the context manager,
    2) receiver fails on enter,
    3) receiver fails on exit.
    """

    def setUp(self):
        self.post_receiver = mock.Mock()
        signals.setting_changed.connect(self.post_receiver)

    def tearDown(self):
        signals.setting_changed.disconnect(self.post_receiver)

    def test_override_settings_both(self):
        """
        Receiver fails on both enter and exit.
        """
        with self.assertRaises(SettingChangeException):
            with override_settings(SETTING_A='X', SETTING_Z='X', SETTING_B='X'):
                pass

        self.assertEquals(settings.SETTING_A, 'A')
        self.assertEquals(settings.SETTING_B, 'B')
        self.assertEquals(settings.SETTING_C, 'C')
        self.assertEquals(settings.SETTING_D, 'D')
        self.assertEquals(settings.SETTING_Z, 'Z')

        post_receiver_calls_on_exit = filter_mock_calls(self.post_receiver.mock_calls, enter=False)
        self.assertEquals(len(list(post_receiver_calls_on_exit)), 3)

    def test_override_settings_enter(self):
        """
        Receiver fails on enter only.
        """
        with self.assertRaises(SettingChangeEnterException):
            with override_settings(SETTING_A='X', SETTING_Z='X', SETTING_C='X'):
                pass

        self.assertEquals(settings.SETTING_A, 'A')
        self.assertEquals(settings.SETTING_B, 'B')
        self.assertEquals(settings.SETTING_C, 'C')
        self.assertEquals(settings.SETTING_D, 'D')
        self.assertEquals(settings.SETTING_Z, 'Z')

        post_receiver_calls_on_exit = filter_mock_calls(self.post_receiver.mock_calls, enter=False)
        self.assertEquals(len(list(post_receiver_calls_on_exit)), 3)

    def test_override_settings_exit(self):
        """
        Receiver fails on exit only.
        """
        with self.assertRaises(SettingChangeExitException):
            with override_settings(SETTING_A='X', SETTING_Z='X', SETTING_D='X'):
                pass

        self.assertEquals(settings.SETTING_A, 'A')
        self.assertEquals(settings.SETTING_B, 'B')
        self.assertEquals(settings.SETTING_C, 'C')
        self.assertEquals(settings.SETTING_D, 'D')
        self.assertEquals(settings.SETTING_Z, 'Z')

        post_receiver_calls_on_exit = filter_mock_calls(self.post_receiver.mock_calls, enter=False)
        self.assertEquals(len(list(post_receiver_calls_on_exit)), 3)
