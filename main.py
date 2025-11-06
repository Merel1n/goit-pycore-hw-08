from collections import UserDict
from datetime import datetime, timedelta
import pickle


class Field:
    """Базовий клас для полів запису"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """Клас для зберігання імені контакту"""
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError ("The name must be more than two characters and not contain numbers.")
        self.value = value
    @staticmethod
    def validate(value):
        """Перевіряє, що ім'я більше 2 символів і не складається з цифер"""
        return len(value) > 2 or not value.isdigit()


class Phone(Field):
    """Клас для зберігання номера телефону з валідацією"""
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Phone number must be in format +<country_code>XXXXXXXXXX")
        super().__init__(value)

    @staticmethod
    def validate(value):
        """паревірка номеру телефону щоб мав формат "+(код країни)10цифр"""
        return (value.startswith("+") or not value[1:].isdigit()) and len(value[1:]) >= 10
    
    
class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        
    def __str__(self):
        # Повертаємо дату у форматі DD.MM.YYYY
        return self.value.strftime("%d.%m.%Y")

class Record:
    """Клас для зберігання інформації про контакт"""
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        """Додає новий номер телефону"""
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        """Видаляє телефон за номером"""
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                break

    def edit_phone(self, old_phone, new_phone):
        """Редагує існуючий номер телефону"""
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
        return f"Contact {self.name} update"

    def find_phone(self, phone):
        """Повертає телефон, якщо він є у списку"""
        for p in self.phones:
            if p.value == phone:
                return p
        return None
    
    def add_birthday(self, birthday):
        """Додає день народження"""
        self.birthday = Birthday(birthday)

    def __str__(self):
        """Гарне текстове представлення запису"""
        phones_str = "; ".join(p.value for p in self.phones) if self.phones else "No phones"
        return f"Contact name: {self.name.value}, phones: {phones_str}"
    
    def __str__(self):
        """Гарне текстове представлення запису"""
        phones_str = "; ".join(p.value for p in self.phones) if self.phones else "No phones"
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"


class AddressBook(UserDict):
    """Клас для зберігання та управління записами"""
    def add_record(self, record):
        """Додає новий запис у книгу"""
        self.data[record.name.value] = record

    def find(self, name):
        """Знаходить запис за ім’ям"""
        return self.data.get(name)

    def delete(self, name):
        """Видаляє запис за ім’ям"""
        if name in self.data:
            del self.data[name]
            
    def get_birthdays_per_week(self):
        """Показує контакти, у яких день народження протягом наступного тижня"""
        today = datetime.now().date()
        week_from_now = today + timedelta(days=7)
        result = []

        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.date().replace(year=today.year)
                if today <= birthday_this_year <= week_from_now:
                    result.append(f"{record.name.value}: {record.birthday}")
        return result


# === ЗБЕРЕЖЕННЯ ТА ЗАВАНТАЖЕННЯ КНИГИ ===

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()
    
    
# === ДЕКОРАТОР ДЛЯ ОБРОБКИ ПОМИЛОК ===

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError:
            return "The data is incorrect. Try again."
        except IndexError:
            return "Enter user name."
    return inner


# === КОМАНДИ ===

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record:
        return record.edit_phone(old_phone, new_phone)
    raise KeyError


@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record:
        phones = ", ".join(p.value for p in record.phones) if record.phones else "No phones"
        return f"{name}'s phones: {phones}"
    raise KeyError


def birthdays(_, book: AddressBook):
    upcoming = book.get_birthdays_per_week()
    if not upcoming:
        return "No birthdays in the next 7 days."
    return "\n".join(upcoming)

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError
    record.add_birthday(birthday)
    return f"Birthday added for {name}."
    

@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is on {record.birthday}"
    else:
        return f"No birthday found for {name}."
    

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args        

def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            # Збереження змін в книзі і вихід з програми
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
           print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            for record in book.data.values():
                print(record)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
