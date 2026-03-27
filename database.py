from sqlalchemy import create_engine # veritabanına bağlanmak için kullanılır.
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = 'sqlite:///./todoai_app.db' # hangi veritabanına bağlanacağımızı belirtir.

# Engine = veritabanı ile bağlantı kuran ana araçtır. uygulama ve veritabanı arasındaki köprğ
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
#Session = veritabanı ile yaptığın işlemleri yöneten oturumdur.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()