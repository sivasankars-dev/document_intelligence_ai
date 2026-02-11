from sqlalchemy import Column, Integer, String, ForeignKey, Text
from shared.database.base import Base


class Document(Base):

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_name = Column(String)
    storage_path = Column(String)
    extracted_text = Column(Text, nullable=True)
    status = Column(String, default="uploaded")
