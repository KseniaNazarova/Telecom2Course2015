import unittest
import SMTP_client

__author__ = 'Ksenia'

HOST = "smtp.mail.ru"
PORT = 465
DOMAIN = "mail.ru"

login = "knazarova9@mail.ru"
password = "Q12345"
email_from = "knazarova9@mail.ru"
email_to = "k-nazarova@mail.ru,knazarova9@yandex.ru"
email_cc = "knazarova9@rambler.ru"
email_bcc = "knazarova9@mail.ru"
subject = "Test"
data = "This is test msg"


class TestSMTP(unittest.TestCase):

    def setUp(self):
        self.smtp = SMTP_client.SMTP(HOST, PORT)

    def test_smtp_successful(self):
        incomplete_login = "knazarova9"

        self.assertEqual(self.smtp.ehlo(DOMAIN), 250, "Fail HELO cmd")
        self.assertEqual(self.smtp.auth(incomplete_login, password), 235, "Fail AUTH cmd")
        self.assertEqual(self.smtp.mail_from(email_from), 250, "Fail MAIL cmd")
        recipients = lambda groups: list(set([email for emails in groups for email in emails]))
        self.assertIn(self.send_to_each_one(recipients([email_to.split(","), email_cc.split(","), email_bcc.split(",")])), [250, 251], "Fail RCPT cmd")
        self.assertEqual(self.smtp.data(email_from, email_to, subject, email_cc, email_bcc, data), 250, "Fail DATA cmd")

    def test_ehlo_failure(self):
        self.assertEqual(self.smtp.ehlo(""), 501, "Should be contain \'Syntax error in parameters\'")

    def test_auth_failure_with_repetition(self):
        nonexistent_login = "~!!~~!!~~!!~"
        wrong_password = "`~!!~~!!~~!!~``"

        self.smtp.ehlo(DOMAIN)
        self.assertEqual(self.smtp.auth(nonexistent_login, wrong_password), 535, "Should be contain \'Authentication credentials invalid\'")
        long_password = "".join("1" for x in range(10000))
        self.assertEqual(self.smtp.auth(login, long_password), 535, "Should be contain \'Authentication credentials invalid\'")

    def test_auth_success_after_failures(self):
        wrong_password = "123123"
        incomplete_login = "knazarova9"

        self.smtp.ehlo(DOMAIN)
        self.assertEqual(self.smtp.auth(login, wrong_password), 535, "Should be contain \'Authentication credentials invalid\'")
        self.assertEqual(self.smtp.auth(incomplete_login, password), 535, "Should be contain \'Authentication credentials invalid\'")
        self.assertEqual(self.smtp.auth(login, password), 235, "Fail AUTH cmd")

    def test_mail_from_failre(self):
        nonexistent_email = "!!~~~!!~~~!!"
        self.smtp.ehlo(DOMAIN)
        self.smtp.auth(login, password)
        self.assertEqual(self.smtp.mail_from(nonexistent_email), 501, "Should be contain \'Syntax error in parameters\'")

    def test_for_wrong_input_sequence_of_cmd(self):
        self.smtp.ehlo(DOMAIN)
        self.smtp.auth(login, password)
        self.assertEqual(self.send_to_each_one(email_cc.split(",")), 503, "Should be contain \'Bad sequence of commands\'")
        self.assertEqual(self.smtp.auth(login, password), 503, "Should be contain \'Bad sequence of commands\'")
        self.smtp.mail_from(email_from)
        self.assertEqual(self.smtp.data(email_from, email_to, subject, email_cc, email_bcc, data), 503, "Should be contain \'Bad sequence of commands\'")
        self.assertIn(self.send_to_each_one(email_cc.split(",")), [250, 251], "Fail RCPT cmd")
        self.assertEqual(self.smtp.data(email_from, email_to, subject, email_cc, email_bcc, data), 250, "Fail DATA cmd")

    def tearDown(self):
        self.smtp.quit()

    def send_to_each_one(self, emails):
        for email in emails:
            resp_code = self.smtp.rcpt_to(email)
            if resp_code != 250 and resp_code != 251:
                break
        return resp_code


class TestSMTPSendMsg(unittest.TestCase):
    def setUp(self):
        self.smtp = SMTP_client.SMTP(HOST, PORT)
        self.smtp.ehlo(DOMAIN)
        self.smtp.auth(login, password)
        self.smtp.mail_from(email_from)

    def test_rcpt_to_failure(self):
        wrong_emails = "----,*&^---,-----"
        recipients = lambda groups: list(set([email for emails in groups for email in emails]))
        self.assertEqual(self.send_to_each_one(recipients([wrong_emails.split(","), wrong_emails.split(","), wrong_emails.split(",")])), 501, "Fail RCPT cmd")

    def test_rcpt_to_many_recipients_successfully(self):
        recipients = lambda groups: list(set([email for emails in groups for email in emails]))
        self.assertIn(self.send_to_each_one(recipients([email_to.split(","), email_cc.split(","), email_bcc.split(",")])), [250, 251], "Fail RCPT cmd")

    def test_create_msg_without_subj(self):
        self.send_to_each_one(email_to.split(","))
        self.assertEqual(self.smtp.data(email_from, email_to), 250, "Fail DATA cmd")
        self.assertWarnsRegex(Warning, "The message can be taken as spam")

    def test_create_msg_successful(self):
        self.send_to_each_one(email_to.split(","))
        self.assertEqual(self.smtp.data(email_from, email_to, subject, data=data), 250, "Fail DATA cmd")

    def test_create_msg_successful(self):
        self.send_to_each_one(email_to.split(","))
        self.assertEqual(self.smtp.data(email_from, email_to, subject, data=data), 250, "Fail DATA cmd")

    def tearDown(self):
        self.smtp.quit()

    def send_to_each_one(self, emails):
        for email in emails:
            resp_code = self.smtp.rcpt_to(email)
            if resp_code != 250 and resp_code != 251:
                break
        return resp_code



