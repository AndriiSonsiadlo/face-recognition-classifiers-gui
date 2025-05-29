class MyPhoto:
	size = 0

	def __init__(self, path: str = ''):
		self.index = self.size
		self.size = self.size + 1
		self.path = path
