class Employee:
    def __init__(self, nickname , lastname , pay):
        self.nickname = nickname
        self.lastname = lastname
        self.pay = pay

class Developer(Employee):
    def __init__(self, nickname , lastname , pay, language):
        super().__init__(nickname, lastname, pay)
        self.language = language


employee_1 = Employee("nina", "smith", 2000)
developer_1 = Developer("nina", "smith", 2000, language="python")
print(employee_1.nickname)