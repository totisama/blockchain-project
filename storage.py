class Storage():
  def __init__(self):
    self.data = {}

  def save(self, nonce, receiver):
    if nonce not in self.data.keys():
      self.data[nonce] = {}

    if receiver in self.data[nonce].keys():
      self.data[nonce][receiver] += 1
    else:
      self.data[nonce][receiver] = 1

  def print_storage(self):
    print(self.data)