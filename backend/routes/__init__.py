def register_blueprints(app):
    from routes.activity_logs import bp as activity_logs_bp
    from routes.admin import bp as admin_bp
    from routes.analytics import bp as analytics_bp
    from routes.auth import bp as auth_bp
    from routes.backup import bp as backup_bp
    from routes.backup_logs import bp as backup_logs_bp
    from routes.comments import bp as comments_bp
    from routes.contributors import bp as contributors_bp
    from routes.follow import bp as follow_bp
    from routes.images import bp as images_bp
    from routes.languages import bp as languages_bp
    from routes.notifications import bp as notifications_bp
    from routes.repositories import bp as repos_bp
    from routes.sessions import bp as sessions_bp
    from routes.snapshots import bp as snapshots_bp
    from routes.stars import bp as stars_bp
    from routes.tags import bp as tags_bp
    from routes.tags import repo_tags_bp
    from routes.users import bp as users_bp
    from routes.github import bp as github_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(repos_bp)
    app.register_blueprint(languages_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(repo_tags_bp)
    app.register_blueprint(contributors_bp)
    app.register_blueprint(follow_bp)
    app.register_blueprint(stars_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(snapshots_bp)
    app.register_blueprint(activity_logs_bp)
    app.register_blueprint(backup_logs_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(github_bp)
