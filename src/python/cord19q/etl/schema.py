"""
Schema module
"""

class Schema(object):
    """
    Defines data structures to store article content
    """

    # Articles schema
    ARTICLES = {
        'Id': 'TEXT PRIMARY KEY',
        'Source': 'TEXT',
        'Published': 'DATETIME',
        'Publication': "TEXT",
        'Authors': 'TEXT',
        'Title': 'TEXT',
        'Tags': 'TEXT',
        'Design': 'INTEGER',
        'Size': 'TEXT',
        'Sample': 'TEXT',
        'Method': 'TEXT',
        'Reference': 'TEXT'
    }

    # Sections schema
    SECTIONS = {
        'Id': 'INTEGER PRIMARY KEY',
        'Article': 'TEXT',
        'Tags': 'TEXT',
        'Design': 'INTEGER',
        'Name': 'TEXT',
        'Text': 'TEXT',
        'Labels': 'TEXT'
    }

    # Stats schema
    STATS = {
        'Id': 'INTEGER PRIMARY KEY',
        'Article': 'TEXT',
        'Section': 'INTEGER',
        'Name': 'TEXT',
        'Value': 'TEXT'
    }

    # Citations schema
    CITATIONS = {
        'Title': 'TEXT PRIMARY KEY',
        'Mentions': 'INTEGER'
    }
