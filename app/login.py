from app.models import Account


class AccountLogin:
    account = None

    def from_db(self, account_id):
        self.account = Account.get(Account.id == account_id)
        return self

    def create(self, account):
        self.account = account
        return self

    def is_authenticated(self):
        if self.account:
            return True
        else:
            return False

    def is_active(self):
        if self.account:
            return True
        else:
            return False

    def is_anonymous(self):
        if self.account:
            return False
        else:
            return True

    def get_id(self):
        account_id = self.account.id
        return str(account_id)
