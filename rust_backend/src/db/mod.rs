//! Database Module - Simplified version
//! SQLite database operations

use anyhow::Result;
use sqlx::{SqlitePool, Row};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub email: Option<String>,
    pub role: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssessmentRecord {
    pub id: i64,
    pub user_id: i64,
    pub video_name: String,
    pub pose_name: String,
    pub total_score: Option<f64>,
    pub structure_score: Option<f64>,
    pub alignment_score: Option<f64>,
    pub stability_score: Option<f64>,
    pub problems: Option<String>,
    pub suggestions: Option<String>,
    pub assessment_time: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoseStandard {
    pub id: i64,
    pub pose_name: String,
    pub hip_min: Option<f64>,
    pub hip_max: Option<f64>,
    pub knee_min: Option<f64>,
    pub knee_max: Option<f64>,
    pub shoulder_min: Option<f64>,
    pub shoulder_max: Option<f64>,
    pub spine_min: Option<f64>,
    pub spine_max: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemStats {
    pub total_assessments: i64,
    pub total_users: i64,
    pub avg_score: f64,
    pub today_assessments: i64,
}

#[derive(Clone)]
pub struct Database {
    pool: SqlitePool,
}

impl Database {
    /// Create new database connection
    pub async fn new(db_path: &str) -> Result<Self> {
        let database_url = format!("sqlite:{}?mode=rwc", db_path);
        let pool = SqlitePool::connect(&database_url).await?;
        
        // Initialize schema
        Self::init_schema(&pool).await?;
        
        // Insert default data
        Self::insert_defaults(&pool).await?;
        
        Ok(Self { pool })
    }

    /// Initialize database schema
    async fn init_schema(pool: &SqlitePool) -> Result<()> {
        // User table
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            )
            "#,
        )
        .execute(pool)
        .await?;

        // Assessment record table
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS assessment_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                video_name TEXT NOT NULL,
                video_path TEXT NOT NULL,
                pose_name TEXT NOT NULL,
                assessment_time TEXT NOT NULL DEFAULT (datetime('now')),
                total_score REAL,
                structure_score REAL,
                alignment_score REAL,
                stability_score REAL,
                angle_data TEXT,
                graph_data TEXT,
                problems TEXT,
                suggestions TEXT,
                annotated_video_path TEXT,
                processing_time REAL,
                model_used TEXT
            )
            "#,
        )
        .execute(pool)
        .await?;

        // Pose standard table
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS pose_standard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pose_name TEXT NOT NULL UNIQUE,
                pose_name_en TEXT,
                category TEXT,
                difficulty_level TEXT,
                hip_min REAL,
                hip_max REAL,
                knee_min REAL,
                knee_max REAL,
                shoulder_min REAL,
                shoulder_max REAL,
                spine_min REAL,
                spine_max REAL,
                description TEXT,
                common_errors TEXT
            )
            "#,
        )
        .execute(pool)
        .await?;

        Ok(())
    }

    /// Insert default data
    async fn insert_defaults(pool: &SqlitePool) -> Result<()> {
        // Insert default admin user (password: admin123)
        sqlx::query(
            r#"
            INSERT OR IGNORE INTO user (username, password, email, role)
            VALUES ('admin', 'admin123', 'admin@example.com', 'admin')
            "#,
        )
        .execute(pool)
        .await?;

        // Insert default pose standards
        let poses = vec![
            ("Mountain Pose", "Tadasana", "Basic", "Beginner", 170.0, 180.0, 165.0, 180.0, 170.0, 180.0, 0.0, 10.0),
            ("Tree Pose", "Vrksasana", "Balance", "Beginner", 150.0, 175.0, 160.0, 180.0, 160.0, 180.0, 0.0, 15.0),
            ("Warrior II", "Virabhadrasana II", "Strength", "Intermediate", 140.0, 170.0, 155.0, 175.0, 160.0, 180.0, 0.0, 20.0),
            ("Triangle Pose", "Trikonasana", "Stretch", "Intermediate", 150.0, 175.0, 160.0, 180.0, 155.0, 180.0, 5.0, 25.0),
            ("Chair Pose", "Utkatasana", "Strength", "Beginner", 130.0, 160.0, 150.0, 175.0, 165.0, 180.0, 0.0, 15.0),
        ];

        for (name, name_en, category, difficulty, hip_min, hip_max, knee_min, knee_max, shoulder_min, shoulder_max, spine_min, spine_max) in poses {
            sqlx::query(
                r#"
                INSERT OR IGNORE INTO pose_standard 
                (pose_name, pose_name_en, category, difficulty_level, hip_min, hip_max, knee_min, knee_max, shoulder_min, shoulder_max, spine_min, spine_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                "#,
            )
            .bind(name)
            .bind(name_en)
            .bind(category)
            .bind(difficulty)
            .bind(hip_min)
            .bind(hip_max)
            .bind(knee_min)
            .bind(knee_max)
            .bind(shoulder_min)
            .bind(shoulder_max)
            .bind(spine_min)
            .bind(spine_max)
            .execute(pool)
            .await?;
        }

        Ok(())
    }

    /// Create new assessment record
    pub async fn create_assessment(
        &self,
        user_id: i64,
        video_name: &str,
        video_path: &str,
        pose_name: &str,
    ) -> Result<i64> {
        let result = sqlx::query(
            r#"
            INSERT INTO assessment_record (user_id, video_name, video_path, pose_name)
            VALUES (?, ?, ?, ?)
            "#,
        )
        .bind(user_id)
        .bind(video_name)
        .bind(video_path)
        .bind(pose_name)
        .execute(&self.pool)
        .await?;

        Ok(result.last_insert_rowid())
    }

    /// Update assessment result
    pub async fn update_assessment_result(
        &self,
        id: i64,
        total_score: f64,
        structure_score: f64,
        alignment_score: f64,
        stability_score: f64,
        problems: &str,
        suggestions: &str,
    ) -> Result<()> {
        sqlx::query(
            r#"
            UPDATE assessment_record 
            SET total_score = ?, structure_score = ?, alignment_score = ?, 
                stability_score = ?, problems = ?, suggestions = ?
            WHERE id = ?
            "#,
        )
        .bind(total_score)
        .bind(structure_score)
        .bind(alignment_score)
        .bind(stability_score)
        .bind(problems)
        .bind(suggestions)
        .bind(id)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    /// Get assessment by ID
    pub async fn get_assessment(&self, id: i64) -> Result<Option<AssessmentRecord>> {
        let row = sqlx::query(
            r#"
            SELECT id, user_id, video_name, pose_name, total_score, 
                   structure_score, alignment_score, stability_score,
                   problems, suggestions, assessment_time
            FROM assessment_record WHERE id = ?
            "#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        Ok(row.map(|r| AssessmentRecord {
            id: r.get("id"),
            user_id: r.get("user_id"),
            video_name: r.get("video_name"),
            pose_name: r.get("pose_name"),
            total_score: r.get("total_score"),
            structure_score: r.get("structure_score"),
            alignment_score: r.get("alignment_score"),
            stability_score: r.get("stability_score"),
            problems: r.get("problems"),
            suggestions: r.get("suggestions"),
            assessment_time: r.get("assessment_time"),
        }))
    }

    /// List recent assessments
    pub async fn list_assessments(&self, limit: i64) -> Result<Vec<AssessmentRecord>> {
        let rows = sqlx::query(
            r#"
            SELECT id, user_id, video_name, pose_name, total_score, 
                   structure_score, alignment_score, stability_score,
                   problems, suggestions, assessment_time
            FROM assessment_record 
            ORDER BY assessment_time DESC 
            LIMIT ?
            "#,
        )
        .bind(limit)
        .fetch_all(&self.pool)
        .await?;

        let records: Vec<AssessmentRecord> = rows
            .into_iter()
            .map(|r| AssessmentRecord {
                id: r.get("id"),
                user_id: r.get("user_id"),
                video_name: r.get("video_name"),
                pose_name: r.get("pose_name"),
                total_score: r.get("total_score"),
                structure_score: r.get("structure_score"),
                alignment_score: r.get("alignment_score"),
                stability_score: r.get("stability_score"),
                problems: r.get("problems"),
                suggestions: r.get("suggestions"),
                assessment_time: r.get("assessment_time"),
            })
            .collect();

        Ok(records)
    }

    /// List pose standards
    pub async fn list_pose_standards(&self) -> Result<Vec<PoseStandard>> {
        let rows = sqlx::query(
            r#"
            SELECT id, pose_name, hip_min, hip_max, knee_min, knee_max,
                   shoulder_min, shoulder_max, spine_min, spine_max
            FROM pose_standard
            ORDER BY id
            "#,
        )
        .fetch_all(&self.pool)
        .await?;

        let standards: Vec<PoseStandard> = rows
            .into_iter()
            .map(|r| PoseStandard {
                id: r.get("id"),
                pose_name: r.get("pose_name"),
                hip_min: r.get("hip_min"),
                hip_max: r.get("hip_max"),
                knee_min: r.get("knee_min"),
                knee_max: r.get("knee_max"),
                shoulder_min: r.get("shoulder_min"),
                shoulder_max: r.get("shoulder_max"),
                spine_min: r.get("spine_min"),
                spine_max: r.get("spine_max"),
            })
            .collect();

        Ok(standards)
    }

    /// Get pose standard by name
    pub async fn get_pose_standard(&self, pose_name: &str) -> Result<Option<PoseStandard>> {
        let row = sqlx::query(
            r#"
            SELECT id, pose_name, hip_min, hip_max, knee_min, knee_max,
                   shoulder_min, shoulder_max, spine_min, spine_max
            FROM pose_standard WHERE pose_name = ?
            "#,
        )
        .bind(pose_name)
        .fetch_optional(&self.pool)
        .await?;

        Ok(row.map(|r| PoseStandard {
            id: r.get("id"),
            pose_name: r.get("pose_name"),
            hip_min: r.get("hip_min"),
            hip_max: r.get("hip_max"),
            knee_min: r.get("knee_min"),
            knee_max: r.get("knee_max"),
            shoulder_min: r.get("shoulder_min"),
            shoulder_max: r.get("shoulder_max"),
            spine_min: r.get("spine_min"),
            spine_max: r.get("spine_max"),
        }))
    }

    /// Get system statistics
    pub async fn get_stats(&self) -> Result<SystemStats> {
        let count_row = sqlx::query(
            r#"
            SELECT COUNT(*) as count, COALESCE(AVG(CAST(total_score AS REAL)), 0.0) as avg_score
            FROM assessment_record WHERE total_score IS NOT NULL
            "#,
        )
        .fetch_one(&self.pool)
        .await?;

        let total_assessments: i64 = count_row.get("count");
        let avg_score: f64 = count_row.get("avg_score");

        let user_count_row = sqlx::query(
            r#"
            SELECT COUNT(*) as count FROM user WHERE is_active = 1
            "#,
        )
        .fetch_one(&self.pool)
        .await?;

        let total_users: i64 = user_count_row.get("count");

        let today_row = sqlx::query(
            r#"
            SELECT COUNT(*) as count FROM assessment_record 
            WHERE DATE(assessment_time) = DATE('now')
            "#,
        )
        .fetch_one(&self.pool)
        .await?;

        let today_assessments: i64 = today_row.get("count");

        Ok(SystemStats {
            total_assessments,
            total_users,
            avg_score,
            today_assessments,
        })
    }

    /// List users (admin only)
    pub async fn list_users(&self) -> Result<Vec<User>> {
        let rows = sqlx::query(
            r#"
            SELECT id, username, email, role, created_at
            FROM user WHERE is_active = 1 ORDER BY created_at DESC
            "#,
        )
        .fetch_all(&self.pool)
        .await?;

        let users: Vec<User> = rows
            .into_iter()
            .map(|r| User {
                id: r.get("id"),
                username: r.get("username"),
                email: r.get("email"),
                role: r.get("role"),
                created_at: r.get("created_at"),
            })
            .collect();

        Ok(users)
    }
}
