#Class that represents all the data that is important from the xml file
class Article:
    def __init__(self, id, title, tags, content, url, blogUrl, issn, template):
        self.id = id
        self.title = title
        self.tags = tags
        self.content = content
        self.url = url
        self.blogUrl = blogUrl
        self.template = template
        self.issn = issn

    def printItems(self):
        print self.id
        print self.title
        print self.tags
        print self.content
        print self.url
        print self.blogUrl
        print self.template
        print self.issn