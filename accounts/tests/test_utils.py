import accounts.utils
from django.contrib.auth.models import User
from django.test import TestCase
from unittest import mock
from accounts.models import Flag, Staff
from accounts.utils import (
    get_flag,
    get_superuser_staff_model,
    reset_password_email_generator,
    send_email_to_user,
    get_or_generate_patient_code,
    get_or_generate_patient_profile_qr
)


class GetFlagTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create(username="patient_user")
        self.staff_user = User.objects.create(username="staff_user")

    def test_user_without_flag(self):
        """
        Test that trying to get a flag that doesn't exist returns None
        @return: void
        """

        # Act & Assert
        self.assertIsNone(get_flag(self.staff_user, self.patient_user))

    def test_user_with_flag(self):
        """
        Test that getting a flag that exists returns the flag
        @return: void
        """

        # Arrange
        flag = Flag.objects.create(patient=self.patient_user, staff=self.staff_user)

        # Act & Assert
        self.assertEqual(flag, get_flag(self.staff_user, self.patient_user))


class GetSuperuserStaffModelTests(TestCase):
    def test_superuser_does_not_exist(self):
        """
        Test that when no superuser exists, the function returns None
        @return: void
        """

        # Act & Assert
        self.assertIsNone(get_superuser_staff_model())

    @mock.patch.object(accounts.utils.Staff.objects, 'create')
    def test_superuser__has_no_staff_object__creates_staff_object(self, m_create_staff_model):
        """
        Test that for a superuser without a staff object, the function o create one for it is called.
        @return: void
        """

        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)

        # Act
        get_superuser_staff_model()

        # Assert
        m_create_staff_model.assert_called_once_with(user=self.superuser)

    def test_superuser__has_no_staff_object__returns_staff_object(self):
        """
        Test that for a superuser without a staff object, one is created and assigned to it, and returned
        @return: void
        """

        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)

        # Act
        result = get_superuser_staff_model()

        # Assert
        self.assertIsInstance(result, Staff)
        self.assertEqual(result, self.superuser.staff)

    def test_superuser__has_staff_object__returns_staff_object(self):
        """
        Test that the staff object of a superuser that already has one gets returned and that a new one isn't created
        @return: void
        """

        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)
        staff_obj = Staff.objects.create(user=self.superuser)
        self.superuser.refresh_from_db()

        # Act & Assert
        self.assertEqual(staff_obj, get_superuser_staff_model())
        self.assertEqual(staff_obj, self.superuser.staff)
        with mock.patch.object(accounts.utils.Staff.objects, 'create') as m_staff_model:
            m_staff_model.assert_not_called()


class ResetEmailPasswordGeneratorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user")
        self.subject = "Test Subject"
        self.template = "Test Template"

    # NOTE: TO ANYONE WHO USES THIS AS INSPIRATION FOR DOING MULTIPLE MOCKS:
    # The decorators wrap the function and are thus loaded in "reverse order"!
    # The decorator in the bottom will populate the first param, second from bottom
    # is the second param, etc. until the first decorator populates the last param.
    @mock.patch('accounts.utils.send_email_to_user')
    @mock.patch('accounts.utils.render_to_string', return_value="email")
    def test_renders_email(self, m_render_function, _):
        """
        Check that the render to string function is being called
        @param m_render_function: render_to_string() function mock
        @param _: send_email_to_user() function mock (not called in test)
        @return: void
        """

        # Act
        reset_password_email_generator(self.user, self.subject, self.template)

        # Assert
        m_render_function.assert_called_once()

    @mock.patch('accounts.utils.render_to_string', return_value="email")
    @mock.patch('accounts.utils.send_email_to_user')
    def test_sends_email(self, m_send_email_function, _):
        """
        Check that the send email function is being called
        @param m_send_email_function: send_email_to_user() function mock
        @param _: render_to_string() function mock (not called in test)
        @return: void
        """

        # Act
        reset_password_email_generator(self.user, self.subject, self.template)

        # Assert
        m_send_email_function.assert_called_once_with(self.user, self.subject, "email")


class SendEmailToUserTests(TestCase):
    @mock.patch('accounts.utils.smtplib')
    def test_send_email(self, m_smtp):
        """
        Check that the smtplib functions are being called
        @param m_smtp: smtplib library mock
        @return: void
        """

        # Arrange
        user = User.objects.create(email="test@email.com")
        m_instance = m_smtp.SMTP.return_value
        sender_email = 'shahdextra@gmail.com'
        sender_pass = 'roses12345!%'
        email_contents = f"Subject: test subject\ntest message"

        # Act
        send_email_to_user(user, "test subject", "test message")

        # Assert
        m_smtp.SMTP.assert_called_once_with('smtp.gmail.com', 587)
        m_instance.starttls.assert_called_once()
        m_instance.login.assert_called_once_with(sender_email, sender_pass)
        m_instance.sendmail.assert_called_once_with(sender_email, user.email, email_contents)
        m_instance.quit.assert_called_once()


class GetOrGenerateCodeTests(TestCase):
    @mock.patch('accounts.utils.Patient')
    @mock.patch('accounts.utils.shortuuid.set_alphabet')
    def test_set_alphabet(self, m_shortuuid_set_alphabet, m_patient):
        """
        Check that the custom alphabet is set correctly
        @param m_shortuuid_set_alphabet: set_alphabet() function mock
        @param m_patient: mock patient object
        @return: void
        """

        # Act
        get_or_generate_patient_code(m_patient)

        # Assert
        m_shortuuid_set_alphabet.assert_called_once_with('23456789ABCDEFGHJKLMNPQRSTUVWXYZ')

    @mock.patch('accounts.utils.shortuuid.set_alphabet')
    @mock.patch('accounts.utils.Patient')
    def test_patient_with_code_returns_code(self, m_patient, _):
        """
        Check that passing a Patient with a code returns the code
        @param m_patient: mock patient object
        @param _: set_alphabet() function mock (not called in test)
        @return: void
        """

        # Arrange
        m_instance = m_patient.return_value
        m_instance.code = 'boxxy'

        # Act
        result = get_or_generate_patient_code(m_instance)

        # Assert
        self.assertEqual('boxxy', result)

    @mock.patch('accounts.utils.Patient.objects')
    @mock.patch('accounts.utils.Patient')
    def test_patient_without_code_returns_new_code(self, m_patient, m_patient_objects):
        """
        Check that passing a Patient without a code generates a new code
        @param m_patient: mock patient object
        @param m_patient_objects: mock patient.objects object
        @return:
        """

        # Arrange
        m_instance = m_patient.return_value
        m_instance.code = None

        # Patient does not have a code
        m_patient_objects.filter().exists.return_value = False

        # Act & Assert
        self.assertIsNotNone(get_or_generate_patient_code(m_instance))


class GenerateProfileQrTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_staff=False)

    def test_user_is_staff_returns_None(self):
        """
        Check that passing a staff user returns None
        @return: void
        """

        # Arrange
        self.user.is_staff = True
        self.user.save()
        self.user.refresh_from_db()

        # Act & Assert
        self.assertIsNone(get_or_generate_patient_profile_qr(self.user.id))

    @mock.patch('accounts.utils.Path.mkdir')
    @mock.patch('accounts.utils.PilImage')
    @mock.patch('accounts.utils.make')
    @mock.patch('accounts.utils.os.path.exists')
    @mock.patch('accounts.utils.get_or_generate_patient_code')
    @mock.patch('accounts.utils.Patient.objects')
    def test_user_is_not_staff_returns_image_path(self, m_patient_objects, m_code_generator, m_os_path_exists,
                                                  m_qrcode_make, m_pil_image, _):
        """
        Check that passing a patient user with an existing qr image returns the path to the image
        @param m_patient_objects: Mock patient object
        @param m_code_generator: Mock patient code generator utility function
        @param m_os_path_exists: Mock os path
        @param m_qrcode_make: Mock qrcode make function that returns a mocked PilImage
        @param m_pil_image: Mock PilImage save function
        @param _:
        @return: void
        """

        cases = [
            {'path_exists': False, 'msg': 'When the qr image does not exist'},
            {'path_exists': True, 'msg': 'When the qr image exists'}
        ]
        for case in cases:
            with self.subTest(case.get('msg')):
                # Arrange
                m_code_generator.return_value = 'boxxy'
                m_patient_objects.get.return_value = None
                m_generated_image = m_pil_image.return_value  # Mock image returned by PilImage
                m_qrcode_make.return_value = m_generated_image  # Making the qrcode returns the mocked PilImage
                m_os_path_exists.return_value = case.get('path_exists')

                # Reset the calls between the test cases
                # (else the fact that it was called will "leak into"
                # the other test case and assert_not_called() will fail)
                m_generated_image.reset_mock()

                # Act
                returned_path = get_or_generate_patient_profile_qr(self.user.id)

                # Assert
                if not case.get('path_exists'):
                    m_generated_image.save.assert_called_once_with('accounts/static/accounts/qrs/boxxy.png')
                else:
                    m_generated_image.save.assert_not_called()

                self.assertEqual('accounts/qrs/boxxy.png', returned_path)
