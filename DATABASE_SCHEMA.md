# 📊 StudyHub Database Schema

## Entity Relationship Diagram

```
┌─────────────────────────────┐
│          USERS              │
├─────────────────────────────┤
│ PK  id                      │
│     username (UNIQUE)       │
│     email (UNIQUE)          │
│     password_hash           │
│     created_at              │
└─────────────────────────────┘
            │
            │ 1
            │
            │ has many
            │
            ▼ *
┌─────────────────────────────┐
│        SUBJECTS             │
├─────────────────────────────┤
│ PK  id                      │
│     name                    │
│     description             │
│     color                   │
│ FK  user_id ────────────────┤ References users(id)
│     created_at              │
└─────────────────────────────┘
            │
            │ 1
            │
            │ has many
            │
            ▼ *
┌─────────────────────────────┐
│          NOTES              │
├─────────────────────────────┤
│ PK  id                      │
│     title                   │
│     content                 │
│ FK  subject_id ─────────────┤ References subjects(id)
│     created_at              │
│     updated_at              │
└─────────────────────────────┘
```

## Relationships

### User → Subject (One-to-Many)
- **Type**: One user can have many subjects
- **Cascade**: Deleting a user deletes all their subjects
- **Access**: `user.subjects` or `subject.user`

### Subject → Note (One-to-Many)
- **Type**: One subject can have many notes
- **Cascade**: Deleting a subject deletes all its notes
- **Access**: `subject.notes` or `note.subject`

### User → Note (Indirect)
- Access user's notes through subjects
- Query: `Note.query.join(Subject).filter(Subject.user_id == user_id)`

## Table Details

### USERS
| Column        | Type        | Constraints          | Description                    |
|---------------|-------------|----------------------|--------------------------------|
| id            | INTEGER     | PRIMARY KEY          | Auto-incrementing ID           |
| username      | VARCHAR(80) | UNIQUE, NOT NULL     | User's display name            |
| email         | VARCHAR(120)| UNIQUE, NOT NULL     | Login email (lowercase)        |
| password_hash | VARCHAR(255)| NOT NULL             | Hashed password (pbkdf2)       |
| created_at    | DATETIME    | NOT NULL             | Account creation timestamp     |

**Indexes:**
- Primary key on `id`
- Unique index on `username`
- Unique index on `email`

---

### SUBJECTS
| Column      | Type         | Constraints              | Description                    |
|-------------|--------------|--------------------------|--------------------------------|
| id          | INTEGER      | PRIMARY KEY              | Auto-incrementing ID           |
| name        | VARCHAR(100) | NOT NULL                 | Subject name                   |
| description | TEXT         | NULLABLE                 | Optional description           |
| color       | VARCHAR(7)   | DEFAULT '#0d6efd'        | Hex color code for UI          |
| user_id     | INTEGER      | FOREIGN KEY, NOT NULL    | References users(id)           |
| created_at  | DATETIME     | NOT NULL                 | Subject creation timestamp     |

**Indexes:**
- Primary key on `id`
- Foreign key on `user_id`

**Constraints:**
- ON DELETE CASCADE (deleting user deletes subjects)

---

### NOTES
| Column     | Type         | Constraints              | Description                    |
|------------|--------------|--------------------------|--------------------------------|
| id         | INTEGER      | PRIMARY KEY              | Auto-incrementing ID           |
| title      | VARCHAR(200) | NOT NULL                 | Note title                     |
| content    | TEXT         | NOT NULL                 | Note content                   |
| subject_id | INTEGER      | FOREIGN KEY, NOT NULL    | References subjects(id)        |
| created_at | DATETIME     | NOT NULL                 | Note creation timestamp        |
| updated_at | DATETIME     | NOT NULL                 | Last modification timestamp    |

**Indexes:**
- Primary key on `id`
- Foreign key on `subject_id`

**Constraints:**
- ON DELETE CASCADE (deleting subject deletes notes)

---

## Query Examples

### Get all subjects for a user
```python
user.subjects.all()
# or
Subject.query.filter_by(user_id=user.id).all()
```

### Get all notes for a subject
```python
subject.notes.all()
# or
Note.query.filter_by(subject_id=subject.id).all()
```

### Get all notes for a user
```python
Note.query.join(Subject).filter(Subject.user_id == user.id).all()
```

### Count notes per subject
```python
subject.notes.count()
# or via property
subject.note_count
```

### Get recent notes
```python
Note.query.join(Subject).filter(
    Subject.user_id == user.id
).order_by(Note.updated_at.desc()).limit(5).all()
```

### Search notes by content
```python
Note.query.join(Subject).filter(
    Subject.user_id == user.id,
    Note.content.contains('search term')
).all()
```

---

## Data Flow

### Creating a Note
```
User (authenticated)
  ↓
Subject (owned by user)
  ↓
Note (belongs to subject)
```

### Deleting a Subject
```
Delete Subject
  ↓
CASCADE DELETE
  ↓
All Notes in Subject (deleted automatically)
```

### Accessing User's Data
```
User
  ↓ user.subjects
[Subject, Subject, ...]
  ↓ subject.notes
[Note, Note, Note, ...]
```

---

## Storage Estimates

Based on average usage:

| Entity    | Avg per User | Size per Record | Total Size (100 users) |
|-----------|--------------|-----------------|------------------------|
| User      | 1            | ~500 bytes      | 50 KB                  |
| Subject   | 10           | ~300 bytes      | 300 KB                 |
| Note      | 50           | ~2 KB           | 10 MB                  |

**Total**: ~10.35 MB for 100 active users

---

## Backup Strategy

### SQLite (Development)
```bash
# Backup
cp studyhub.db studyhub_backup.db

# Restore
cp studyhub_backup.db studyhub.db
```

### PostgreSQL (Production)
```bash
# Backup
pg_dump studyhub > backup.sql

# Restore
psql studyhub < backup.sql
```

---

**Database Version**: Phase 3  
**Last Updated**: February 2024  
**Schema Version**: 1.0.0
