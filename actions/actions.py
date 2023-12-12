from datetime import datetime
from typing import Any, Text, List
from rasa_sdk import Tracker, Action, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet

from actions.const import MENU, OPENING_HOURS

class ActionValidateOrder(FormValidationAction):
    
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
                invalid_items.append(item.lower())
            else:
                valid_items.append(item.lower())
                
        if invalid_items:
            dispatcher.utter_message(f"{', '.join(invalid_items)} items are not in the menu. Please select from menu.")
           
        if valid_items:
            dispatcher.utter_message(f"{', '.join(valid_items)} added to the order.")
            return {"food_items": valid_items}

        dispatcher.utter_message("Please enter valid items from menu!")
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
    
    def name(self) -> Text:
        return "action_return_week_hours"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ):
        query_time =  tracker.get_slot("times")
        query_day: str = tracker.get_slot("days")
        today =  datetime.now().weekday()
        today_name = list(OPENING_HOURS.keys())[today]
        
        if not query_time and not query_day:
            timetable = ',\n'.join([
                * [
                    f"{key}: {value['open']}-{value['close']}" 
                    for key, value in OPENING_HOURS.items()
                    if not value['open'] == value['close'] == 0
                ],
                *[
                   f"{key}: closed" 
                    for key, value in OPENING_HOURS.items()
                    if value['open'] == value['close'] == 0 
                ]   
            ])
            
            dispatcher.utter_message(f"We are open in the following days: \n{timetable}")
        
        elif query_time and not query_day:
            
            if query_time in ["now", "today"]:
                _day = OPENING_HOURS.get(today_name)
                print(_day)
                if _day['open'] == _day['close'] == 0:
                    dispatcher.utter_message(f"We are sorry but today we are closed.")
                else:
                    dispatcher.utter_message(f"Today we are open from {_day['open']} to {_day['close']}")
            else:
                today = today +1 if today < 6 else 0
                today_name = list(OPENING_HOURS.keys())[today]
                _day = OPENING_HOURS.get(today_name)
                print(_day)
                if _day['open'] == _day['close'] == 0:
                    dispatcher.utter_message(f"We are sorry but today we are closed.")
                else:
                    dispatcher.utter_message(f"Tomorrow we are open from {_day['open']} to {_day['close']}")
                
        elif query_day:
            _day = OPENING_HOURS.get(query_day.capitalize())
            print(_day)
            if _day['open'] == _day['close'] == 0:
                dispatcher.utter_message(f"We are sorry but on {query_day} we are closed.")
            else:
                dispatcher.utter_message(f"On {query_day} we are open from {_day['open']} to {_day['close']}")
            
        else:
            dispatcher.utter_message(f"Sorry I didn't understand the question,  could you repeat?")
            
        return [ SlotSet("days", None), SlotSet("times", None) ]
        


class ActionOrderSummary(Action):
    
    _text: str
    
    def name(self) -> Text:
        return "action_return_order_summary"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ):
        food_items = tracker.get_slot("food_items")
        delivery_at_house = tracker.get_slot("delivery_home")
        foods = ',\n'.join(food_items)
        address = tracker.get_slot("address")
        total: int = sum([
            item["price"] 
            for item in MENU 
            if item["name"].lower() in food_items
        ])
        hr_ready: int = sum([
            item["preparation_time"] * 60 
            for item in MENU 
            if item["name"].lower() in food_items
        ])
        
        if delivery_at_house:
            dispatcher.utter_message(
                f"You have ordered: \n{foods} \n "
                f"the order will be delivered in {hr_ready+30} minutes"
                f"at the address {address}, "
                f"the total price is €{total}."
            )
        else:
            dispatcher.utter_message(
                f"You have ordered: \n{foods} \n "
                f"the order will be ready in {hr_ready} minutes,"
                f"the total price is €{total}."
            )
            
        return [ 
            SlotSet("food_items", None),
            SlotSet("delivery_home", None),
            SlotSet("address", None),
            SlotSet("address_confirmed", None),
        ]