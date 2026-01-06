import os


structure = {
    ".env": "",
    "requirements.txt": "",
    "main_launcher.py": "",
    "core": {
        "__init__.py": "",
        "config.py": "",
        "database.py": "",
        "fuzzy_logic.py": ""
    },
    "agents": {
        "__init__.py": "",
        "agent_1_detector.py": "",
        "agent_2_brain.py": "",
        "agent_3_notifier.py": ""
    },
    "backend": {
        "app.py": "",
        "routes.py": ""
    },
    "frontend": {
        "public": {},
        "src": {
            "components": {
                "HmiPanel.jsx": "",
                "AlertLog.jsx": ""
            },
            "App.jsx": "",
            "main.jsx": ""
        },
        "vite.config.js": ""
    }
}


def create_structure(base_path, tree):
    for name, content in tree.items():
        path = os.path.join(base_path, name)

        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


if __name__ == "__main__":
    os.makedirs("../", exist_ok=True)
    create_structure("../", structure)
    print("✅ Proyecto SERPIENTE creado con éxito, causa.")
