from dataclasses import dataclass

@dataclass
class EraContext:
    era_name: str
    era_description: str
    known_projects: list[str]
    unknown_future_events: list[str]

class TimelineHandler:
    INDIA_ERA_CONTEXT = {
        (1940, 1955): EraContext(
            era_name="Early Career & Independence",
            era_description="""
India is newly independent. Prime Minister Jawaharlal Nehru's concept of the 'scientific temper' is the guiding national philosophy. The country is overwhelmingly agrarian, struggling with poverty and the aftermath of Partition. However, there is immense optimism. Dr. Homi Bhabha and you are laying the very first bricks of India's scientific institutions. There are no indigenous computers, no space programme, and formal scientific research is confined to a few pockets. You are focusing on cosmic rays, traveling between Cambridge and India, and establishing the Physical Research Laboratory (PRL) in Ahmedabad in 1947.
""",
            known_projects=["Physical Research Laboratory (PRL)", "Cosmic Ray Research", "Ahmedabad Textile Industry's Research Association (ATIRA)"],
            unknown_future_events=["The launch of Sputnik (1957)", "The establishment of INCOSPAR (1962)", "The Apollo Moon Landing (1969)"]
        ),
        (1956, 1965): EraContext(
            era_name="The Space Era Dawns",
            era_description="""
The Cold War space race is accelerating globally following the launch of Sputnik. In India, the first nuclear reactor (APSARA) went critical in 1956. You successfully advocate for a space research program, leading to the formation of INCOSPAR in 1962. The geopolitical situation is tense, particularly after the 1962 Sino-Indian war, which sharpens the national focus on self-reliance and defense. You establish the Thumba Equatorial Rocket Launching Station (TERLS) in Kerala, launching the first Nike-Apache sounding rocket in 1963 with the help of a local church. You are deeply engaged with NASA and the Soviet space agencies, navigating non-alignment while securing vital training and equipment.
""",
            known_projects=["INCOSPAR", "Thumba Equatorial Rocket Launching Station (TERLS)", "Indian Institute of Management Ahmedabad (IIMA)"],
            unknown_future_events=["The creation of ISRO (1969)", "The tragic death of Homi Bhabha (1966)", "The SITE Experiment (1975)"]
        ),
        (1966, 1971): EraContext(
            era_name="Institution Building at Peak Influence",
            era_description="""
Following the sudden death of Homi Bhabha in 1966, you have taken on the immense responsibility of chairing the Atomic Energy Commission in addition to leading the space programme. ISRO is formally established in 1969. IIM Ahmedabad is recognized as a world-class management institution. You are heavily involved in defense, electronics, and national planning. Your focus has shifted towards massive, national-scale applications of technology, such as using satellites for nationwide television broadcasting to educate rural farmers (the SITE project). You are initiating the development of indigenous launch vehicles (SLV) and satellites (Aryabhata). The burden is heavy, but your vision of a technologically leapfrogging India is materializing.
""",
            known_projects=["ISRO", "Atomic Energy Commission", "Satellite Instructional Television Experiment (SITE)", "Satellite Launch Vehicle (SLV) planning"],
            unknown_future_events=["The launch of Aryabhata (1975)", "Your own untimely death in December 1971", "The successful SITE broadcast"]
        )
    }
    
    SARABHAI_TIMELINE = {
        1919: "Born on August 12 in Ahmedabad to a wealthy industrialist family.",
        1937: "Leaves for Cambridge, England, to study natural sciences at St. John's College.",
        1940: "Returns to India due to World War II; joins the Indian Institute of Science (IISc) in Bangalore to work under Sir C.V. Raman.",
        1942: "Marries classical dancer Mrinalini Swaminathan.",
        1945: "Returns to Cambridge after the war to complete his PhD.",
        1947: "Returns to an independent India. Founds the Physical Research Laboratory (PRL) in Ahmedabad. Helps establish the Ahmedabad Textile Industry's Research Association (ATIRA).",
        1949: "Founds the Darpana Academy of Performing Arts with Mrinalini.",
        1957: "Launch of Sputnik by the USSR; Sarabhai keenly observes the potential of space technology.",
        1962: "Convinces the government to establish the Indian National Committee for Space Research (INCOSPAR).",
        1962: "Establishes the Indian Institute of Management Ahmedabad (IIMA).",
        1963: "Establishes the Thumba Equatorial Rocket Launching Station (TERLS) near Trivandrum.",
        1963: "November 21: First sounding rocket (Nike-Apache) launched from Thumba.",
        1966: "Appointed Chairman of the Atomic Energy Commission (AEC) following the death of Homi Bhabha.",
        1966: "Establishes the Community Science Centre in Ahmedabad.",
        1967: "Appointed Chairman of the newly formed Electronics Committee.",
        1968: "Dedicates TERLS to the United Nations as an international facility.",
        1969: "INCOSPAR is superseded by the Indian Space Research Organisation (ISRO).",
        1969: "Signs agreement with NASA for the Satellite Instructional Television Experiment (SITE).",
        1971: "Dies unexpectedly on December 30 at Kovalam, Kerala, at the age of 52."
    }
    
    def get_era_context(self, year: int) -> EraContext:
        """Returns the EraContext for a given year, or None if outside handled ranges."""
        for year_range, context in self.INDIA_ERA_CONTEXT.items():
            if year_range[0] <= year <= year_range[1]:
                return context
        return None
        
    def build_temporal_constraint(self, year: int) -> str:
        """Builds a string instructing the model to act as if it is a specific year."""
        context = self.get_era_context(year)
        if not context:
            return ""
            
        constraint = [
            f"IMPORTANT TEMPORAL CONSTRAINT: You are speaking from the year {year}. ",
            f"You do NOT have any knowledge of events, technologies, or people that became prominent after {year}. ",
            "If asked about the future, speculate based only on what was known at the time.\n",
            f"Active projects right now: {', '.join(context.known_projects)}.\n",
            "Specifically, you do NOT know about the following future events (DO NOT mention them): "
        ]
        constraint.append(", ".join(context.unknown_future_events) + ".")
        
        return "".join(constraint)
