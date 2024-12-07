
                    if entity_id not in self.power_structure.entities:
                        # New entity
                        entity = self.power_structure.add_entity(
                            id=entity_id,
                            name=entity_data.get("name", entity_id),
                            entity_type=entity_data.get("type", "unknown"),
                            properties=properties
                        )
                        
                        # Add to timeline
                        self.timeline.add_event({
                            "type": "entity_created",
                            "entity_id": entity_id,
                            "timestamp": datetime.now(UTC)
                        })
                    else:
                        # Update existing entity
                        entity = self.power_structure.entities[entity_id]
                        for key, value in properties.items():
                            entity.update_property(
                                key=key,
                                value=value.value,
                                source=source_type,
                                confidence=confidence
                            )
                            
                            # Add update to timeline
                            self.timeline.add_event({
                                "type": "entity_updated",
                                "entity_id": entity_id,
                                "property": key,
                                "timestamp": datetime.now(UTC)
                            })
        
        # Process relationships
        if "relationships" in content:
            for rel in content["relationships"]:
                self._process_relationship(rel, source_type, confidence)
        
        # Save checkpoint
        self._save_checkpoint()