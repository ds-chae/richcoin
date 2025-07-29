import pymysql

conn = pymysql.connect(host='localhost', port=3306, user='coinuser', passwd='richcoin!@!', db='richcoin', charset='utf8')
print('connected')
conn.close()
print('finished')
