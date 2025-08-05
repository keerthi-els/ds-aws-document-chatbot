import streamlit_authenticator as stauth

hashed_passwords = stauth.Hasher.hash_list(['your_password'])
print(hashed_passwords)
