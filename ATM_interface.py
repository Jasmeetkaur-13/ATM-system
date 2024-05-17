import sqlite3
import getpass
from datetime import datetime

class User:
    def __init__(self, user_id, pin, balance_inr=0):
        self.user_id = user_id
        self.pin = pin
        self.balance_inr = balance_inr

class ATM:
    MAX_LOGIN_ATTEMPTS = 3

    def __init__(self):
        self.conn = sqlite3.connect('atm.db')
        self.create_users_table()
        self.current_user = None

    def create_users_table(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                      (user_id TEXT PRIMARY KEY, pin TEXT, balance_inr REAL, locked INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS transactions
                      (user_id TEXT, transaction_type TEXT, amount REAL, timestamp DATETIME)''')
        self.conn.commit()

    def create_account(self):
        user_id = input("Enter Your Account Number: ")
        if self.account_exists(user_id):
            print("Account Previously Created.")
        else:
            pin = getpass.getpass("Create Your Account PIN: ")
            self.insert_user(user_id, pin)
            print("You Have Successfully Created an Account!")

    def account_exists(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return c.fetchone() is not None

    def insert_user(self, user_id, pin):
        c = self.conn.cursor()
        c.execute("INSERT INTO users (user_id, pin, balance_inr, locked) VALUES (?, ?, 0, 0)",
                  (user_id, pin))
        self.conn.commit()

    def login(self):
        if self.current_user is not None:
            print("Logout required before switching accounts.")
            return

        user_id = input("Enter your account number: ")
        if not self.account_exists(user_id):
            print("User does not exist.")
            return

        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()

        if user[3]: 
            print("This account is locked. Contact customer support for assistance.")
            return

        attempts = 0
        while attempts < self.MAX_LOGIN_ATTEMPTS:
            pin = getpass.getpass("Enter your PIN: ")
            if pin == user[1]: 
                self.current_user = User(user[0], user[1], user[2])
                print("Login was successful!")
                return
            else:
                attempts += 1
                print(f"Invalid PIN. {self.MAX_LOGIN_ATTEMPTS - attempts} Remaining Attempts.")

        
        c.execute("UPDATE users SET locked = 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()
        print("Login failed. Account locked due to multiple unsuccessful attempts. Contact customer support for assistance..")

    def record_transaction(self, transaction_type, amount):
        c = self.conn.cursor()
        timestamp = datetime.now()
        c.execute("INSERT INTO transactions (user_id, transaction_type, amount, timestamp) VALUES (?, ?, ?, ?)",
                  (self.current_user.user_id, transaction_type, amount, timestamp))
        self.conn.commit()

    def main_menu(self):
        while True:
            if self.current_user is None:
                print('ATM INTERFACE')
                print('Select an option:')
                print('1. Create Account')
                print('2. Login')
                print('3. Quit')
                response = input('Enter the number of your choice (1/2/3): ')
                if response == '1':
                    self.create_account()
                elif response == '2':
                    self.login()
                elif response == '3':
                    print("Goodbye! Have a great day!")
                    exit()
                else:
                    print('Your choice is invalid. Please select from the provided options.')
            else:
                print('ATM INTERFACE')
                print('Select an option:')
                print('1. TRANSACTIONS HISTORY')
                print('2. WITHDRAW')
                print('3. DEPOSIT')
                print('4. CHANGE PIN')
                print('5. TRANSFER')
                print('6. LOGOUT')
                response = input('Enter the number of your choice (1/2/3/4/5/6): ')

                valid_responses = ['1', '2', '3', '4', '5', '6']
                if response in valid_responses:
                    if response == '1':
                        self.print_statement()
                    elif response == '2':
                        self.withdraw()
                    elif response == '3':
                        self.deposit()
                    elif response == '4':
                        self.change_pin()
                    elif response == '5':
                        self.transfer()
                    elif response == '6':
                        self.logout()
                        print("Goodbye! Have a great day!")
                        break
                else:
                    print('Your choice is invalid. Please select from the provided options.')

    def withdraw(self):
        print('---------------')
        print('***************')
        amount = int(input('Enter the amount to withdraw: '))

        if amount % 10 != 0:
            print('Amount should be in increments of 30 rupee notes.')
        elif amount > self.current_user.balance_inr:
            print('Your balance is too low for this transaction.')
        else:
            self.current_user.balance_inr -= amount
            self.record_transaction("Withdraw", amount)
            print('Updated balance: ', self.current_user.balance_inr, 'Rupees')

    def deposit(self):
        print()
        print('---------------')
        print('***************')
        amount = int(input('Enter deposit amount: '))

        if amount % 10 != 0:
            print('Amount should be in increments of 30 rupee notes.')
        else:
            self.current_user.balance_inr += amount
            self.record_transaction("Deposit", amount)
            print('Balance after transaction: ', self.current_user.balance_inr, 'Rupees')

    def change_pin(self):
        print('-----------')
        print('***********')
        new_pin = str(getpass.getpass('Enter a New PIN: '))
        print('***********')
        if new_pin.isdigit() and new_pin != self.current_user.pin and len(new_pin) == 4:
            print('------')
            print('******')
            new_ppin = str(getpass.getpass('Verify new PIN: '))
            print('*******')
            if new_ppin != new_pin:
                print('----------')
                print('****')
                print('Incorrect PIN confirmation')
                print('****')
                print('----------')
            else:
                c = self.conn.cursor()
                c.execute("UPDATE users SET pin = ? WHERE user_id = ?", (new_pin, self.current_user.user_id))
                self.conn.commit()
                self.current_user.pin = new_pin
                print('PIN successfully updated')
        else:
            print('-------------')
            print('*************')
            print('Your new PIN should be 4 digits /n and cannot match your previous PIN')
            print('*************')
            print('--------------')

    def transfer(self):
        if self.current_user is None:
            print("Please log in to proceed with money transfer.")
            return

        source_account = input("Enter your account number: ")
        destination_account = input("Enter the account number of the recipient:: ")
        amount = int(input("Enter the amount to transfer: "))

        if amount % 10 != 0:
            print('The transfer amount should be in increments of 30 rupee notes.')
        elif amount > self.current_user.balance_inr:
            print('You Have Insufficient Balance')
        else:
            destination_user = self.get_user_by_id(destination_account)
            if destination_user is not None:
                self.current_user.balance_inr -= amount
                self.record_transaction("Transfer (Out)", amount)

                destination_user.balance_inr += amount
                self.record_transaction("Transfer (In)", amount)
                print('Transaction successful')
            else:
                print('Account not found for the recipient')

    def print_statement(self):
        print('-----------')
        print('***********')
        print(str.capitalize(self.current_user.user_id), 'YOU HAVE ', self.current_user.balance_inr, 'RUPEES ON YOUR ACCOUNT.')
        print('***********')
        print('------------')
        self.record_transaction("Statement", 0)

    def logout(self):
        self.current_user = None
        print("Logged out successfully!")

    def get_user_by_id(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        else:
            return None


conn = sqlite3.connect('atm.db')
conn.close()


atm = ATM()


while True:
    print('-----------')
    print('*********')
    response = input('Please select from the following options:\n'
                     'Create Account (C) \n'
                     'Login (L) \n'
                     'Quit (Q) \n'
                     'Please enter the letter corresponding to your choice: ').lower()
    print('*********')
    print('---------')

    valid_responses = ['c', 'l', 'q']
    response = response.lower()
    if response == 'c':
        atm.create_account()
    elif response == 'l':
        atm.login()
        atm.main_menu()
    elif response == 'q':
        print("Goodbye! Have a great day!")
        exit()
    else:
        print('-------')
        print('******')
