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

    def __str__(self):
        print self.id+"|"+self.title+"|"+str(self.tags)+"|"+self.content+"|"+self.url+"|"+self.blogUrl+"|"+self.template+"|"+self.issn