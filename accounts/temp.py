import smtplib

subject = "Welcome to Covigo!"
message = "Love, Shahd - Mo - Amir - Nizar - Shu - Avg - Isaac - Justin - Aseel"
s = smtplib.SMTP('smtp.gmail.com', 587)
s.starttls()
email = 'shahdextra@gmail.com'
pwd = 'roses12345!%'
s.login(email,pwd)
#f"Subject: {subject}\n{content}"
s.sendmail(email, 'shahdyousefak@gmail.com', f"Subject: {subject}\n{message}")
s.quit()