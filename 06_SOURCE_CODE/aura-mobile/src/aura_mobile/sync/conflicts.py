def resolve(local,remote):
 if local.version>remote.version:return local
 if remote.version>local.version:return remote
 return remote if str(remote.payload)>=str(local.payload) else local
