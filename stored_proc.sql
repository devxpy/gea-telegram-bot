DROP TRIGGER send_email_on_appointment ON appointments_appointment;
DROP FUNCTION send_email;

CREATE FUNCTION send_email()
  RETURNS trigger
AS $$
    plan = plpy.prepare("SELECT first_name, email FROM users_customuser WHERE id = $1", ['integer'])
    user = plpy.execute(plan, [TD['new']['user_id']])[0]

    msg = (
        'Hello, ' +
        user['first_name'] +
        '.\n\nYour service appointment has been booked successfully.\n\n' +
        'Our service executive will reach out to you shortly.\n\n' +
        'Appointment tracking number - ' + TD['new']['tracking_number']
    )

    import subprocess
    subprocess.Popen([
        '/Users/dev/.virtualenvs/gea_bot-574a05b1/bin/python',
        '/Users/dev/Projects/gea_bot/scripts/send_email.py',
        user['email'],
        msg
    ])
$$ LANGUAGE plpythonu;

CREATE TRIGGER send_email_on_appointment
    AFTER INSERT ON appointments_appointment
    FOR EACH ROW
    EXECUTE PROCEDURE send  _email();
