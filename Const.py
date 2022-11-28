from datetime import datetime, date, timedelta
 
class Const: 
    BANKNIFTY = [
        {'date': date(2022, 12, 1)}
        ,{'date': date(2022, 12, 8)}
        ,{'date': date(2022, 12, 15)}
        ,{'date': date(2022, 12, 22)}
        ,{'date': date(2022, 12, 29)}

        ,{'date': date(2023, 1, 5)}
        ,{'date': date(2023, 1, 12)}
        ,{'date': date(2023, 1, 19)}
        ,{'date': date(2023, 1, 25)}

        ,{'date': date(2023, 2, 2)}
        ,{'date': date(2023, 2, 9)}
        ,{'date': date(2023, 2, 16)}
        ,{'date': date(2023, 2, 23)}
    ]

    def get_banknifry_expiry(self, cur_date:date):
        indx = 0
        
        while (self.BANKNIFTY[indx]['date'] < cur_date):
            indx += 1

        return self.BANKNIFTY[indx]['date']





    


    
 


