import type { ClaimSummary } from "@/types";

export const DEMO_CLAIMS: ClaimSummary[] = [
  {
    id: 0,
    user_id: "user_005",
    claim_object: "car",
    user_claim:
      "Customer: Need to file a car damage claim. | Agent: What part of the car? | Customer: Door. | Agent: Scratch, dent, or paint issue? | Customer: A deep dent on the door panel. It was not there before.",
    image_count: 2,
    image_paths: "images/test/case_003/img_1.jpg;images/test/case_003/img_2.jpg",
  },
  {
    id: 1,
    user_id: "user_018",
    claim_object: "laptop",
    user_claim:
      "Customer: The laptop screen cracked after it fell from my desk. | Support: Is the crack visible in the uploaded photos? | Customer: Yes, the screen crack is clear.",
    image_count: 3,
    image_paths: "images/test/case_012/img_1.jpg;images/test/case_012/img_2.jpg;images/test/case_012/img_3.jpg",
  },
  {
    id: 2,
    user_id: "user_021",
    claim_object: "package",
    user_claim:
      "Customer: The package arrived crushed on one side. | Support: Are the box and label visible? | Customer: Yes, both images show the damaged box.",
    image_count: 2,
    image_paths: "images/test/case_018/img_1.jpg;images/test/case_018/img_2.jpg",
  },
  {
    id: 3,
    user_id: "user_004",
    claim_object: "car",
    user_claim:
      "Customer: A stone hit the front glass while driving. | Support: Are you reporting the windshield? | Customer: Yes. It looks shattered from my side.",
    image_count: 2,
    image_paths: "images/test/case_004/img_1.jpg;images/test/case_004/img_2.jpg",
  },
  {
    id: 4,
    user_id: "user_027",
    claim_object: "laptop",
    user_claim:
      "Customer: The hinge feels broken and the lid does not close properly. | Support: Please upload clear images. | Customer: I added close-ups of the hinge.",
    image_count: 1,
    image_paths: "images/test/case_026/img_1.jpg",
  },
  {
    id: 5,
    user_id: "user_031",
    claim_object: "package",
    user_claim:
      "Customer: The seal was torn when the delivery arrived. | Support: Is the contents claim included? | Customer: No, only torn packaging.",
    image_count: 2,
    image_paths: "images/test/case_031/img_1.jpg;images/test/case_031/img_2.jpg",
  },
];
