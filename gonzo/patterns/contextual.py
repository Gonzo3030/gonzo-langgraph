
            # Process specific relationship types
            if "influence" in rel:
                self.power_structure.learn_influence_relationship(
                    source_id,
                    target_id,
                    rel["influence"].get("strength", 0.5),
                    source_type,
                    confidence
                )
            
            if "financial" in rel:
                self.power_structure.learn_financial_relationship(
                    source_id,
                    target_id,
                    rel["financial"],
                    source_type,
                    confidence
                )
            
            if "policy_alignment" in rel:
                self.power_structure.learn_policy_alignment(
                    source_id,
                    target_id,
                    rel["policy_alignment"].get("score", 0.5),
                    rel["policy_alignment"].get("topics", [])
                )