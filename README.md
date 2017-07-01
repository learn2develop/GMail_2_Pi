# Communicating with Raspberry Pi via email
+ Sending command via email to your Raspberry Pi

# Requirements
+ Gmail account
+ Define allowed email addresses into ALLOWED = []
+ Define EMAIL address for Raspberry Pi to probe
+ Define PASSWORD for the email address password
+ Define SUBJECT with triggering subject string

# Process
1. Send email to the email address with trigger header to the defined email address from allowed email
2. Wait for the reply with the key
3. Copy the key into clipboard
4. Press reply and paste the key string behind the existing subject text in the subject field
5. Type on the end of the subject the text of the command
6. Send the message
