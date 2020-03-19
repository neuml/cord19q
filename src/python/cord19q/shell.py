"""
cord19 query shell module.
"""

from cmd import Cmd

from .query import Query

class Shell(Cmd):
    """
    cord19 query shell.
    """

    intro = "cord19 query shell"
    prompt = "(c19q) "
    embeddings = None
    db = None

    def preloop(self):
        # Load embeddings and questions.db
        self.embeddings, self.db = Query.load()

    def postloop(self):
        if self.db:
            self.db.close()

    def default(self, line):
        Query.query(self.embeddings, self.db, line)

def main():
    """
    Shell execution loop.
    """

    Shell().cmdloop()

if __name__ == "__main__":
    main()
