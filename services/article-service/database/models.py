from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func, Table
from sqlalchemy.orm import relationship
from .database import Base

# 用户表
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

    articles = relationship("Article", back_populates="author")
    comments = relationship("Comment", back_populates="user")

# 文章表
class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    author = relationship("User", back_populates="articles")
    comments = relationship("Comment", back_populates="article")
    tags = relationship("Tag", secondary="article_tags", back_populates="articles", lazy = "selectin")

# 评论表
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    article = relationship("Article", back_populates="comments")
    user = relationship("User", back_populates="comments")

# 标签表
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    articles = relationship("Article", secondary="article_tags", back_populates="tags" , lazy = "selectin")

# 文章-标签关联表
article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
