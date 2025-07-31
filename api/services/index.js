export default function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET");
  
  const mockServices = [
    { id: 1, name: "Mount Isa Base Hospital", category: "Health Services", description: "Major regional hospital" },
    { id: 2, name: "Gidgee Healing", category: "Health Services", description: "Indigenous health service" },
    { id: 3, name: "PCYC Mount Isa", category: "Youth Support", description: "Youth development programs" }
  ];
  
  res.json(mockServices);
}
