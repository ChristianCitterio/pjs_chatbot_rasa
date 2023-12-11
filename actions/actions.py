from datetime import datetime
from typing import Any, Text, List
from rasa_sdk import Tracker, Action, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet

from actions.const import MENU, OPENING_HOURS

class ActionValidateOrder(FormValidationAction):
    
    total_price: int
    del_hour: int
    
    def name(self) -> Text:
        return "action_save_order"

    def validate_food_items(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ):
        menu_items: List[str] = [ item["name"].lower() for item in MENU ]
        valid_items = []
        invalid_items = []
        for item in slot_value:
            if item.lower() not in menu_items:
                invalid_items.append(item)
            else:
                valid_items.append(item)
                
        if invalid_items:
            dispatcher.utter_message(f"{', '.join(invalid_items)} items are not in the menu. Please select from menu.")
           
        if valid_items:
            self.total_price += (int(item["price"]) for item in MENU)
            self.del_hour += (int(item["preparation_time"] * 60) for item in MENU) 
            dispatcher.utter_message(f"{', '.join(valid_items)} added to the order.")
            SlotSet("final_price", str(self.total_price))
            SlotSet("when_is_ready", str(self.del_hour))
            return {"food_items": valid_items}

        return {"food_items": None}


class ActionShowMenu(Action):
    
    def name(self) -> Text:
        return "action_return_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ):
        menu_items = [ f"{item['name']}: €{item['price']}" for item in MENU]
        textified_menu = ",\n".join(menu_items)
        
        dispatcher.utter_message(f"Our menu is: \n{textified_menu}")
        return
    
    
class ActionShowHours(Action):
    
    day: str = datetime.now().weekday()
    
    def name(self) -> Text:
        return "action_return_week_hours"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ):
        query_time =  tracker.get_slot("times")
        query_day = tracker.get_slot("days")
        
        if not query_time and not query_day:
            timetable = ',\n'.join(
                [f"{key}: {value['']}-{value['']}" for key, value in OPENING_HOURS.items()]
            )
            
            dispatcher.utter_message(f"We are open in the following days: \n{timetable}")
        
        elif query_time and not query_day:
            
            if query_time in ["now", "today"]:
                _day = OPENING_HOURS.get(OPENING_HOURS.keys()[self.day])
                dispatcher.utter_message(f"Today we are open from {_day['open']} to {_day['close']}")
            if query_time == "Tomorrow":
                _day = ""
                if self.day < 6:
                    _day = OPENING_HOURS.get(OPENING_HOURS.keys()[self.day + 1])
                else:
                    _day = OPENING_HOURS.get(OPENING_HOURS.keys()[0])
                
                dispatcher.utter_message("Tomorrow we are open from {_day['open']} to {_day['close']}")
                
        elif query_day:
            _day = OPENING_HOURS.get(query_day)
            dispatcher.utter_message(f"On {_day}'s we are open from {_day['open']} to {_day['close']}")
            
        else:
            dispatcher.utter_message(f"Sorry I didn't understand the question,  could you repeat?")
            
        return


class ActionOrderSummary(Action):
    
    _text: str
    
    def name(self) -> Text:
        return "action_return_week_hours"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ):
        total =  tracker.get_slot("final_price")
        hr_ready = tracker.get_slot("when_is_ready")
        delivery_at_house = tracker.get_slot("delivery_home")
        foods = ',\n'.join(tracker.get_slot("food_items"))
        address = tracker.get_slot("address")
        
        if delivery_at_house:
            dispatcher.utter_message(
                f"You have ordered: \n{foods} \n "
                f"the order will be delivered at {hr_ready+30} "
                f"at the address {address}, "
                f"the total price is €{total}."
            )
        else:
            dispatcher.utter_message(
                f"You have ordered: \n{foods} \n "
                f"the order will be ready at {hr_ready+30} "
                f"the total price is €{total}."
            )
            
        return