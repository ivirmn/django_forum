from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(key)  # Сохраните этот ключ в ваших настройках
#b'YG_9o1NJ2VvU7pQhmxMifPGSiXpmHy82_0Lpn26PXf4='