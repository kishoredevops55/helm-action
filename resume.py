from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Data for reordering
skill_categories = {
    "Programming Languages": ["Python", "Shell Scripting", "Groovy"],
    "DevOps Tools": ["Jenkins", "GitLab CI", "GitHub Actions", "Docker", "Kubernetes", "Ansible"],
    "Cloud Platforms": ["AWS", "Azure"],
    "Monitoring": ["Prometheus", "Grafana", "ELK Stack", "Datadog"]
}

education_entries = [
    {"degree": "B.Tech in Computer Science", "institution": "Anna University", "year": "2015", "score": "8.5 CGPA"}
]

projects = [
    "CI/CD pipeline setup for microservices architecture using Jenkins and Kubernetes.",
    "Infrastructure monitoring with Prometheus and Grafana.",
    "Automation of deployment processes using Ansible and Terraform."
]

# Creating a new Document
doc_reordered = Document()

# Title and Contact Information
doc_reordered.add_heading('KISHORE SHARMA', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle = doc_reordered.add_heading('Senior Software Engineer', level=1)
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
contact_info = doc_reordered.add_paragraph(
    "Phone: (+91) 8015002126 | Email: kisaron5@gmail.com | Location: Chennai, India | LinkedIn: linkedin.com/in/kishore-sharma-sundaram-260a18120/"
)
contact_info.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Professional Summary
doc_reordered.add_heading('Professional Summary', level=2)
doc_reordered.add_paragraph(
    "- Highly skilled SRE and DevOps Engineer with over 7 years of experience in CI/CD automation, software configuration management, and infrastructure management.\n"
    "- Expertise in implementing and supporting CI/CD pipelines, build & release management, and automation infrastructure for monitoring.\n"
    "- Proficient in various DevOps and cloud platforms, with a focus on enhancing system reliability and operational efficiency."
)

# Work Experience with updated sequence
doc_reordered.add_heading('Work Experience', level=2)

experiences_reordered = [
    {
        "position": "Sr Software Engineer - Cognizant",
        "dates": "11/2023 - Present",
        "responsibilities": [
            "Managed observability platforms for continuous monitoring, enhancing detection accuracy by 30%.",
            "Developed CI/CD pipelines with GitHub Actions and Jenkins, reducing deployment time by 50%.",
            "Managed microservices on AKS, improving resource utilization by 20%.",
            "Used Grafana Enterprise for metrics and tracing, increasing troubleshooting efficiency by 40%.",
            "Enhanced productivity with GitHub Copilot and VS Code."
        ]
    },
    {
        "position": "Technical Lead - HCL Technologies",
        "dates": "06/2021 - 11/2023",
        "responsibilities": [
            "Led CI/CD implementation and observability practices, improving system reliability and deployment speed.",
            "Managed Jenkins and Ansible automation, streamlining pipeline processes across teams.",
            "Conducted migration projects, including Bitbucket to GitLab and Azure Git to GitHub, using automated solutions."
        ]
    },
    {
        "position": "Senior DevOps Engineer - Walmart",
        "dates": "03/2021 - 06/2021",
        "responsibilities": [
            "Configured Jenkins CI/CD for application deployments, improving release consistency."
        ]
    },
    {
        "position": "Senior DevOps Engineer - Accenture",
        "dates": "03/2020 - 03/2021",
        "responsibilities": [
            "Improved CI/CD stability by enhancing build and release management processes."
        ]
    },
    {
        "position": "Senior Infra Developer - Cognizant",
        "dates": "05/2019 - 03/2020",
        "responsibilities": [
            "Assisted clients with CI/CD implementation, focusing on DevOps development and support.",
            "Built and managed automation infrastructure with advanced monitoring tools.",
            "Ensured process adherence to SCM standards across projects, contributing to system stability."
        ]
    },
    {
        "position": "Software Engineer - Virtusa",
        "dates": "12/2015 - 05/2019",
        "responsibilities": [
            "Developed efficient build and deployment processes as part of the DevOps team."
        ]
    }
]

for job in experiences_reordered:
    p = doc_reordered.add_paragraph()
    p.add_run(f"{job['position']} ({job['dates']})").bold = True
    for responsibility in job['responsibilities']:
        doc_reordered.add_paragraph(f"   - {responsibility}", style='List Bullet')

# Key Skills and Tools
doc_reordered.add_heading('Key Skills & Tools', level=2)

for category, skills in skill_categories.items():
    p = doc_reordered.add_paragraph()
    p.add_run(f"{category}: ").bold = True
    p.add_run(", ".join(skills))

# Education Section
doc_reordered.add_heading('Education', level=2)

for edu in education_entries:
    p = doc_reordered.add_paragraph()
    p.add_run(f"{edu['degree']} - {edu['institution']} ({edu['year']})")
    if "score" in edu:
        p.add_run(f", Score: {edu['score']}")

# Projects Section
doc_reordered.add_heading('Projects', level=2)

for project in projects:
    doc_reordered.add_paragraph(f"- {project}", style='List Bullet')

# Languages Section
doc_reordered.add_heading('Languages', level=2)
doc_reordered.add_paragraph("Tamil, English")

# Save the reordered resume
output_path_reordered_docx = "/mnt/data/Kishore_Resume_Final_Reordered.docx"
doc_reordered.save(output_path_reordered_docx)

output_path_reordered_docx
