from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, DECIMAL, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class DeviceType(enum.Enum):
    desktop = "desktop"
    tablet = "tablet"
    mobile = "mobile"

class TestStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class ProjectRole(enum.Enum):
    owner = "owner"
    member = "member"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255))
    name = Column(String(255), nullable=False)
    google_id = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="owner")
    project_memberships = relationship("ProjectMember", back_populates="user")
    tests = relationship("Test", back_populates="creator")
    comparisons = relationship("Comparison", back_populates="user")  
    comments = relationship("Comment", back_populates="user")
    sent_notifications = relationship("Notification", foreign_keys="Notification.sender_id", back_populates="sender")
    received_notifications = relationship("Notification", foreign_keys="Notification.receiver_id", back_populates="receiver")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    figma_url = Column(String(500))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project")
    baseline_images = relationship("BaselineImage", back_populates="project")
    tests = relationship("Test", back_populates="project")
    comparisons = relationship("Comparison", back_populates="project")  
    notifications = relationship("Notification", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(SQLEnum(ProjectRole), default=ProjectRole.member)
    joined_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")

class BaselineImage(Base):
    __tablename__ = "baseline_images"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    cloudinary_url = Column(String(500), nullable=False)  
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="baseline_images")
    tests = relationship("Test", back_populates="baseline_image")

class Comparison(Base):
    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Thông tin ảnh
    image1_url = Column(String(500), nullable=False)  
    image2_url = Column(String(500), nullable=False)  
    result_image_url = Column(String(500))  
    heatmap_image_url = Column(String(500))  
    
    # Thông tin so sánh
    similarity_score = Column(DECIMAL(5, 2), nullable=False)  
    differences_count = Column(Integer, default=0)
    comparison_method = Column(String(50))  
    target_url = Column(String(500))  
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="comparisons")
    user = relationship("User", back_populates="comparisons")

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    baseline_id = Column(Integer, ForeignKey("baseline_images.id"), nullable=False)
    name = Column(String(255), nullable=False)
    target_url = Column(String(500))
    device = Column(SQLEnum(DeviceType), default=DeviceType.desktop)
    status = Column(SQLEnum(TestStatus), default=TestStatus.pending)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="tests")
    baseline_image = relationship("BaselineImage", back_populates="tests")
    creator = relationship("User", back_populates="tests")
    results = relationship("TestResult", back_populates="test")
    comments = relationship("Comment", back_populates="test")

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    actual_image_url = Column(String(500))  
    diff_image_url = Column(String(500))
    ssim_score = Column(DECIMAL(4, 3))
    has_differences = Column(Boolean, default=False)
    differences_count = Column(Integer, default=0)
    ocr_diff_text = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    test = relationship("Test", back_populates="results")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    test = relationship("Test", back_populates="comments")
    user = relationship("User", back_populates="comments")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_notifications")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_notifications")
    project = relationship("Project", back_populates="notifications")