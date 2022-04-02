# Generated by Django 4.0.2 on 2022-04-02 04:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_profile_preferences'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='patient',
            options={'permissions': [('message_doctor', 'Can compose a new message with the assigned doctor'), ('dashboard_doctor', "Can view the assigned doctor's contact information (name, email, phone number) in dashboard"), ('view_own_code', 'Can view their own QR and patient code')]},
        ),
        migrations.AlterModelOptions(
            name='profile',
            options={'permissions': [('edit_self', 'Can edit their own user'), ('cancel_appointment', 'Can cancel an appointment'), ('edit_password', 'Can change their own password while logged in'), ('edit_username', 'Can change their username'), ('edit_name', 'Can change their first and last name'), ('edit_email', 'Can change their email address'), ('edit_phone', 'Can change their phone number'), ('edit_address', 'Can change their address and postal code'), ('system_message_preference', 'Can change their system message preference'), ('status_deadline_reminder_preference', 'Can change their status update deadline reminder preference'), ('appointment_reminder_preference', 'Can change their appointment reminder preference')]},
        ),
        migrations.AlterModelOptions(
            name='staff',
            options={'permissions': [('is_doctor', 'Staff member is a doctor user'), ('flag_assigned', 'Can flag assigned patients'), ('flag_patients', 'Can flag any patient'), ('flag_view_all', 'Can view all assigned flags'), ('create_patient', 'Can add a patient user'), ('create_user', 'Can add any user'), ('edit_assigned', 'Can edit assigned patients'), ('edit_patient', 'Can edit any patient'), ('edit_user', 'Can edit any user'), ('remove_availability', 'Can delete an appointment availability'), ('manage_groups', 'Can create a new group or edit existing groups'), ('assign_group', "Can change a new or existing user's assigned groups"), ('message_assigned', 'Can compose a new message with assigned patients'), ('message_patient', 'Can compose a new message with any patient'), ('message_user', 'Can compose a new message with any user'), ('create_symptom', 'Can create a symptom'), ('edit_symptom', 'Can edit a symptom'), ('enable_symptom', 'Can enable or disable a symptom'), ('assign_symptom_assigned', 'Can assign symptoms to assigned patients'), ('assign_symptom_patient', 'Can assign symptoms to any patient'), ('update_symptom_assigned', 'Can update assigned symptoms for assigned patients'), ('update_symptom_patient', 'Can update assigned symptoms for any patient'), ('dashboard_covigo_data', 'Can view Covigo case data in dashboard'), ('dashboard_external_data', 'Can view external case data in dashboard'), ('view_patient_code', "Can view any patient's QR and patient code"), ('view_patient_confirmed', "Can view any patient's confirmed status"), ('view_patient_negative', "Can view any patient's latest test status (negative or must test)"), ('view_patient_quarantine', "Can view any patient's quarantine status"), ('set_patient_case', "Can change any patient's case status (confirmed and latest test)"), ('set_patient_quarantine', "Can change any patient's quarantine status"), ('view_patient_test_report', "Can view any patient's test report"), ('view_assigned_code', "Can view an assigned patient's QR and patient code"), ('view_assigned_confirmed', "Can view an assigned patient's confirmed status"), ('view_assigned_negative', "Can view an assigned patient's latest test status (negative or must test)"), ('view_assigned_quarantine', "Can view an assigned patient's quarantine status"), ('set_assigned_case', "Can change an assigned patient's case status (confirmed and latest test)"), ('set_assigned_quarantine', "Can change an assigned patient's quarantine status"), ('view_assigned_test_report', "Can view an assigned patient's test report"), ('view_assigned_doctor', "Can view any patient's assigned doctor"), ('edit_assigned_doctor', 'Can reassign a patient to any other doctor'), ('view_assigned_patients', "Can view a doctor's assigned patients"), ('view_manager', 'Can access the Manager page'), ('view_user_list', 'Can access the Accounts page'), ('edit_preference_user', "Can edit another user's preferences")]},
        ),
    ]
