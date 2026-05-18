import reflex as rx

class CaseStudyState(rx.State):
    project: dict = {}
    not_found: bool = False

    def load_project(self):
        slug = self.router.page.params.get("slug", "")
        from harun_site.utils.data_manager import get_project_by_slug
        p = get_project_by_slug(slug)
        if p is None:
            self.not_found = True
            self.project = {}
        else:
            self.not_found = False
            self.project = p

    @rx.var
    def project_tags(self) -> list[str]:
        return self.project.get("tags", []) if self.project else []

    @rx.var
    def project_name(self) -> str:
        return self.project.get("name", "") if self.project else ""

    @rx.var
    def cs_problem(self) -> str:
        return self.project.get("case_study", {}).get("problem", "") if self.project else ""

    @rx.var
    def cs_architecture(self) -> str:
        return self.project.get("case_study", {}).get("architecture", "") if self.project else ""

    @rx.var
    def cs_stack_reason(self) -> str:
        return self.project.get("case_study", {}).get("stack_reason", "") if self.project else ""

    @rx.var
    def cs_challenges(self) -> str:
        return self.project.get("case_study", {}).get("challenges", "") if self.project else ""

    @rx.var
    def cs_learnings(self) -> str:
        return self.project.get("case_study", {}).get("learnings", "") if self.project else ""
