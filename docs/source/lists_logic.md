# Lists Logic

## Introduction

Portfolio’s [User Data](./rest_api.md#user-data) API endpoint is dedicated to deliver information from Portfolio to external websites. This document describes the implemented logic for creating the lists of the response object.

## Logic

If not specified otherwise, the following applies:

- Each category is sorted chronologically (most recent object on top).

The information transmitted is structured as follows:

1.  **documents/publications**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_document_publication`

    The object **documents/publications** is divided into the following subcategories. Each subcategory is sorted chronologically (most recent publication on top):

    - **monographs**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_monograph`  
      Logic: If object is member of collection `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_monograph` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/author`

    - **composite volumes**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_composite_volume`  
      Logic: If object is member of collection `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_composite_volume` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/editor`

    - **articles**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_article`  
      Logic: If object is member of collection `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_article` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/author`

    - **chapters**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_chapter`  
      Logic: If object is member of collection `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_chapter` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/author`

    - **reviews**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_review`  
      Logic: If object is member of `collection http://base.uni-ak.ac.at/portfolio/taxonomy/collection_review` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/author`

    - **general documents/publications**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_general_document_publication`  
      Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_document_publication` and not already mentioned above and user has any role

2.  **research and projects**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_research_project`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_research_project` and user has any role, except `http://base.uni-ak.ac.at/portfolio/taxonomy/teaching_project_teaching_research_project` with role `http://base.uni-ak.ac.at/portfolio/vocabulary/project_lead`

3.  **awards and grants**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_awards_and_grants`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_awards_and_grants` and user has any role

4.  **fellowships and visiting affiliations**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_fellowship_visiting_affiliation`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_fellowship_visiting_affiliation` and user has any role

5.  **exhibitions**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_exhibition`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_exhibition` and user has any role

6.  **teaching**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_teaching`

    The object **teaching** is divided into the following subcategories:

    - **supervision of theses**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_supervision_of_theses`  
      Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_supervision_of_theses` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/expertizing` or `http://base.uni-ak.ac.at/portfolio/vocabulary/supervisor`

    - **teaching**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_teaching`  
      Logic:
      - If object is part of collection `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_teaching` or `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_education_qualification` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/lecturer`
      - If object type is `http://base.uni-ak.ac.at/portfolio/taxonomy/teaching_project_teaching_research_project` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/project_lead`

7.  **conferences & symposia**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference` and user has any role and entry is not part of **teaching** or **education & qualification**

8.  **conference contributions**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference_contribution`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_conference_contribution` and user has any role

9.  **architecture**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_architecture`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_architecture` and user has any role

10. **audios**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_audio`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_audio` and user has any role

11. **concerts**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_concert`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_concert` and user has any role

12. **design**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_design`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_design` and user has any role

13. **education & qualification**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_education_qualification`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_education_qualification` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/attendance`

14. **functions & practice**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_functions_practice`

    The object **functions & practice** is divided into the following subcategories:

    - **memberships**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_membership`  
      Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_event` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/member` or `http://base.uni-ak.ac.at/portfolio/vocabulary/board_member` or `http://base.uni-ak.ac.at/portfolio/vocabulary/advisory_board`

    - **expert functions**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_expert_function`  
      Logic: - If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_event` and user has role `http://base.uni-ak.ac.at/portfolio/vocabulary/expertizing` or `http://base.uni-ak.ac.at/portfolio/vocabulary/committee_work`

    - **visual and verbal presentations**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_visual_verbal_presentation`  
      Logic: - If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_visual_verbal_presentation` and user has any role

    - **general functions & practice**  
      Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/general_function_and_practice`  
      Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_event` and not already mentioned above and user has any role

15. **festivals**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_festival`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_festival` and user has any role

16. **images**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_image`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_image` and user has any role

17. **performances**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_performance`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_performance` and user has any role

18. **sculptures**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_sculpture`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_sculpture` and user has any role

19. **softwares**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_software`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_software` and user has any role

20. **films/videos**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_film_video`  
    Logic: If object is member of `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_film_video` and user has any role

21. **general activities**  
    Label: `http://base.uni-ak.ac.at/portfolio/taxonomy/collection_general_activity`  
    Logic: All remaining entries, that are not displayed in another category and user has any role, will be shown here.
