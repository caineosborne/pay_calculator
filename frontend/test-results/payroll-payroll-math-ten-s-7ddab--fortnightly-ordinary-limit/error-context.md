# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: payroll.spec.js >> payroll math: ten shifts that exceed the fortnightly ordinary limit
- Location: e2e/payroll.spec.js:75:3

# Error details

```
Error: 
shifts=[{"week":1,"day":"Monday","start":9,"end":17,"break":0},{"week":1,"day":"Tuesday","start":9,"end":17,"break":0},{"week":1,"day":"Wednesday","start":9,"end":17,"break":0},{"week":1,"day":"Thursday","start":9,"end":17,"break":0},{"week":1,"day":"Friday","start":9,"end":17,"break":0},{"week":2,"day":"Monday","start":9,"end":17,"break":0},{"week":2,"day":"Tuesday","start":9,"end":17,"break":0},{"week":2,"day":"Wednesday","start":9,"end":17,"break":0},{"week":2,"day":"Thursday","start":9,"end":17,"break":0},{"week":2,"day":"Friday","start":9,"end":17,"break":0}]
expected={"ordinary":76,"overtime":4,"penaltyPay":0,"gross":2460,"rows":[{"key":"1-Monday","day":"Monday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Monday","start":9,"end":17,"break":0}]},{"key":"1-Tuesday","day":"Tuesday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Tuesday","start":9,"end":17,"break":0}]},{"key":"1-Wednesday","day":"Wednesday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Wednesday","start":9,"end":17,"break":0}]},{"key":"1-Thursday","day":"Thursday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Thursday","start":9,"end":17,"break":0}]},{"key":"1-Friday","day":"Friday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Friday","start":9,"end":17,"break":0}]},{"key":"2-Monday","day":"Monday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":2,"day":"Monday","start":9,"end":17,"break":0}]},{"key":"2-Tuesday","day":"Tuesday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":2,"day":"Tuesday","start":9,"end":17,"break":0}]},{"key":"2-Wednesday","day":"Wednesday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":2,"day":"Wednesday","start":9,"end":17,"break":0}]},{"key":"2-Thursday","day":"Thursday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":2,"day":"Thursday","start":9,"end":17,"break":0}]},{"key":"2-Friday","day":"Friday","worked":8,"ordinary":4,"overtime":4,"shifts":[{"week":2,"day":"Friday","start":9,"end":17,"break":0}]}]}

expect(locator).toBeVisible() failed

Locator: getByText('Period Overtime')
Expected: visible
Error: strict mode violation: getByText('Period Overtime') resolved to 2 elements:
    1) <td class="px-2 py-1 whitespace-nowrap text-sm text-gray-600">Period Overtime</td> aka getByRole('cell', { name: 'Period Overtime' }).first()
    2) <td class="px-2 py-1 whitespace-nowrap text-sm text-gray-600">Period Overtime</td> aka getByRole('cell', { name: 'Period Overtime' }).nth(1)

Call log:
  
- shifts=[{"week":1,"day":"Monday","start":9,"end":17,"break":0},{"week":1,"day":"Tuesday","start":9,"end":17,"break":0},{"week":1,"day":"Wednesday","start":9,"end":17,"break":0},{"week":1,"day":"Thursday","start":9,"end":17,"break":0},{"week":1,"day":"Friday","start":9,"end":17,"break":0},{"week":2,"day":"Monday","start":9,"end":17,"break":0},{"week":2,"day":"Tuesday","start":9,"end":17,"break":0},{"week":2,"day":"Wednesday","start":9,"end":17,"break":0},{"week":2,"day":"Thursday","start":9,"end":17,"break":0},{"week":2,"day":"Friday","start":9,"end":17,"break":0}]
expected={"ordinary":76,"overtime":4,"penaltyPay":0,"gross":2460,"rows":[{"key":"1-Monday","day":"Monday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Monday","start":9,"end":17,"break":0}]},{"key":"1-Tuesday","day":"Tuesday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Tuesday","start":9,"end":17,"break":0}]},{"key":"1-Wednesday","day":"Wednesday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Wednesday","start":9,"end":17,"break":0}]},{"key":"1-Thursday","day":"Thursday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Thursday","start":9,"end":17,"break":0}]},{"key":"1-Friday","day":"Friday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":1,"day":"Friday","start":9,"end":17,"break":0}]},{"key":"2-Monday","day":"Monday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":2,"day":"Monday","start":9,"end":17,"break":0}]},{"key":"2-Tuesday","day":"Tuesday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":2,"day":"Tuesday","start":9,"end":17,"break":0}]},{"key":"2-Wednesday","day":"Wednesday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":2,"day":"Wednesday","start":9,"end":17,"break":0}]},{"key":"2-Thursday","day":"Thursday","worked":8,"ordinary":8,"overtime":0,"shifts":[{"week":2,"day":"Thursday","start":9,"end":17,"break":0}]},{"key":"2-Friday","day":"Friday","worked":8,"ordinary":4,"overtime":4,"shifts":[{"week":2,"day":"Friday","start":9,"end":17,"break":0}]}]} with timeout 5000ms
  - waiting for getByText('Period Overtime')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - generic [ref=e6]: $
      - generic [ref=e7]:
        - paragraph [ref=e8]: Fortnightly pay estimate
        - heading "Pay Checker" [level=1] [ref=e9]
        - paragraph [ref=e10]: Calculate your fortnightly earnings
      - generic [ref=e11]:
        - button "Copy Previous Week" [ref=e12] [cursor=pointer]
        - button "Set to 9-5" [ref=e13] [cursor=pointer]
        - button "Clear All" [ref=e14] [cursor=pointer]
  - main [ref=e16]:
    - region "Pay details" [ref=e17]:
      - generic [ref=e18]:
        - generic [ref=e19]:
          - generic [ref=e20]:
            - generic [ref=e21]: Hourly Rate ($)
            - spinbutton "Hourly Rate ($)" [ref=e22]: "30"
          - generic [ref=e23]:
            - generic [ref=e24]: Award
            - combobox "Award" [ref=e25]:
              - option "Hospitality Award" [selected]
              - option "Aged Care Award"
              - option "Woolworths 2024 EBA"
              - option "Woolworths 2024 EBA (Allocation Demo)"
              - option "Woolworths 2024 EBA (Auto)"
              - option "Woolworths 2024 EBA (Combined)"
              - option "Child Care Award"
              - option "Nurses & Midwives Award"
              - option "Queensland Health EB11"
              - option "Clerks Private Sector Award"
              - option "Auto ChildCare"
          - generic [ref=e26]:
            - generic [ref=e27]: Worker Type
            - generic [ref=e28]:
              - generic [ref=e29]:
                - button "Shift Worker" [ref=e30]
                - button "Day Worker" [ref=e31]
              - button "Show Rules" [ref=e32]
        - generic [ref=e33]:
          - generic [ref=e34]:
            - generic [ref=e35]: Employment Type
            - generic [ref=e36]:
              - button "Full Time" [ref=e37]
              - button "Part Time" [ref=e38]
              - button "Casual" [ref=e39]
          - generic [ref=e40]:
            - generic [ref=e41]: Contracted Hours per Week
            - generic [ref=e42]: Not applicable for casual workers
        - generic [ref=e43]:
          - generic [ref=e44]:
            - generic [ref=e45]: Rule Configuration
            - combobox "Rule Configuration" [ref=e46]:
              - 'option "Built-in: Hospitality Award" [selected]'
          - button "Edit rule configuration" [ref=e47]
    - region "Fortnightly shift entries" [ref=e48]:
      - text: Your fortnight · use 0–6 for next-day times
      - table [ref=e49]:
        - rowgroup [ref=e50]:
          - row [ref=e51]:
            - columnheader "Fortnight Day" [ref=e52]
            - columnheader "Start" [ref=e53]
            - columnheader "End" [ref=e54]
            - columnheader "Break (hrs)" [ref=e55]
            - columnheader "Manual OT" [ref=e56]
            - columnheader "Manual ORD" [ref=e57]
            - columnheader "Public Holiday" [ref=e58]
            - columnheader "Total Hours" [ref=e59]
            - columnheader "ORD Hours" [ref=e60]
            - columnheader "OT Hours" [ref=e61]
            - columnheader "Applied Rules" [ref=e62]
        - rowgroup [ref=e63]:
          - row [ref=e64]:
            - cell "Week 1 - Monday" [ref=e65]
            - cell [ref=e66]:
              - generic [ref=e67]:
                - button "Decrease Monday start time" [ref=e68]: −
                - textbox "Week 1 Monday primary shift start" [ref=e69]: "9"
                - button "Increase Monday start time" [ref=e70]: +
            - cell [ref=e71]:
              - generic [ref=e72]:
                - button "Decrease Monday end time" [ref=e73]: −
                - textbox "Week 1 Monday primary shift end" [ref=e74]: "17"
                - button "Increase Monday end time" [ref=e75]: +
            - cell [ref=e76]:
              - generic [ref=e77]:
                - spinbutton "Week 1 Monday primary unpaid break hours" [ref=e78]: "0"
                - generic [ref=e79]:
                  - button "Clear" [ref=e80]
                  - button "Copy Prev" [disabled] [ref=e81]
                  - button "+ Add shift" [ref=e82]
            - cell [ref=e83]:
              - checkbox "Week 1 Monday manual overtime" [ref=e84]
            - cell [ref=e85]:
              - checkbox "Week 1 Monday manual ordinary" [ref=e86]
            - cell [ref=e87]:
              - checkbox "Week 1 Monday public holiday" [ref=e88]
            - cell "8.00" [ref=e89]
            - cell "8.00" [ref=e90]
            - cell "0.00" [ref=e91]
            - cell "-" [ref=e92]
          - row [ref=e93]:
            - cell "Week 1 - Tuesday" [ref=e94]
            - cell [ref=e95]:
              - generic [ref=e96]:
                - button "Decrease Tuesday start time" [ref=e97]: −
                - textbox "Week 1 Tuesday primary shift start" [ref=e98]: "9"
                - button "Increase Tuesday start time" [ref=e99]: +
            - cell [ref=e100]:
              - generic [ref=e101]:
                - button "Decrease Tuesday end time" [ref=e102]: −
                - textbox "Week 1 Tuesday primary shift end" [ref=e103]: "17"
                - button "Increase Tuesday end time" [ref=e104]: +
            - cell [ref=e105]:
              - generic [ref=e106]:
                - spinbutton "Week 1 Tuesday primary unpaid break hours" [ref=e107]: "0"
                - generic [ref=e108]:
                  - button "Clear" [ref=e109]
                  - button "Copy Prev" [ref=e110]
                  - button "+ Add shift" [ref=e111]
            - cell [ref=e112]:
              - checkbox "Week 1 Tuesday manual overtime" [ref=e113]
            - cell [ref=e114]:
              - checkbox "Week 1 Tuesday manual ordinary" [ref=e115]
            - cell [ref=e116]:
              - checkbox "Week 1 Tuesday public holiday" [ref=e117]
            - cell "8.00" [ref=e118]
            - cell "8.00" [ref=e119]
            - cell "0.00" [ref=e120]
            - cell "-" [ref=e121]
          - row [ref=e122]:
            - cell "Week 1 - Wednesday" [ref=e123]
            - cell [ref=e124]:
              - generic [ref=e125]:
                - button "Decrease Wednesday start time" [ref=e126]: −
                - textbox "Week 1 Wednesday primary shift start" [ref=e127]: "9"
                - button "Increase Wednesday start time" [ref=e128]: +
            - cell [ref=e129]:
              - generic [ref=e130]:
                - button "Decrease Wednesday end time" [ref=e131]: −
                - textbox "Week 1 Wednesday primary shift end" [ref=e132]: "17"
                - button "Increase Wednesday end time" [ref=e133]: +
            - cell [ref=e134]:
              - generic [ref=e135]:
                - spinbutton "Week 1 Wednesday primary unpaid break hours" [ref=e136]: "0"
                - generic [ref=e137]:
                  - button "Clear" [ref=e138]
                  - button "Copy Prev" [ref=e139]
                  - button "+ Add shift" [ref=e140]
            - cell [ref=e141]:
              - checkbox "Week 1 Wednesday manual overtime" [ref=e142]
            - cell [ref=e143]:
              - checkbox "Week 1 Wednesday manual ordinary" [ref=e144]
            - cell [ref=e145]:
              - checkbox "Week 1 Wednesday public holiday" [ref=e146]
            - cell "8.00" [ref=e147]
            - cell "8.00" [ref=e148]
            - cell "0.00" [ref=e149]
            - cell "-" [ref=e150]
          - row [ref=e151]:
            - cell "Week 1 - Thursday" [ref=e152]
            - cell [ref=e153]:
              - generic [ref=e154]:
                - button "Decrease Thursday start time" [ref=e155]: −
                - textbox "Week 1 Thursday primary shift start" [ref=e156]: "9"
                - button "Increase Thursday start time" [ref=e157]: +
            - cell [ref=e158]:
              - generic [ref=e159]:
                - button "Decrease Thursday end time" [ref=e160]: −
                - textbox "Week 1 Thursday primary shift end" [ref=e161]: "17"
                - button "Increase Thursday end time" [ref=e162]: +
            - cell [ref=e163]:
              - generic [ref=e164]:
                - spinbutton "Week 1 Thursday primary unpaid break hours" [ref=e165]: "0"
                - generic [ref=e166]:
                  - button "Clear" [ref=e167]
                  - button "Copy Prev" [ref=e168]
                  - button "+ Add shift" [ref=e169]
            - cell [ref=e170]:
              - checkbox "Week 1 Thursday manual overtime" [ref=e171]
            - cell [ref=e172]:
              - checkbox "Week 1 Thursday manual ordinary" [ref=e173]
            - cell [ref=e174]:
              - checkbox "Week 1 Thursday public holiday" [ref=e175]
            - cell "8.00" [ref=e176]
            - cell "8.00" [ref=e177]
            - cell "0.00" [ref=e178]
            - cell "-" [ref=e179]
          - row [ref=e180]:
            - cell "Week 1 - Friday" [ref=e181]
            - cell [ref=e182]:
              - generic [ref=e183]:
                - button "Decrease Friday start time" [ref=e184]: −
                - textbox "Week 1 Friday primary shift start" [ref=e185]: "9"
                - button "Increase Friday start time" [ref=e186]: +
            - cell [ref=e187]:
              - generic [ref=e188]:
                - button "Decrease Friday end time" [ref=e189]: −
                - textbox "Week 1 Friday primary shift end" [ref=e190]: "17"
                - button "Increase Friday end time" [ref=e191]: +
            - cell [ref=e192]:
              - generic [ref=e193]:
                - spinbutton "Week 1 Friday primary unpaid break hours" [ref=e194]: "0"
                - generic [ref=e195]:
                  - button "Clear" [ref=e196]
                  - button "Copy Prev" [ref=e197]
                  - button "+ Add shift" [ref=e198]
            - cell [ref=e199]:
              - checkbox "Week 1 Friday manual overtime" [ref=e200]
            - cell [ref=e201]:
              - checkbox "Week 1 Friday manual ordinary" [ref=e202]
            - cell [ref=e203]:
              - checkbox "Week 1 Friday public holiday" [ref=e204]
            - cell "8.00" [ref=e205]
            - cell "6.00" [ref=e206]
            - cell "2.00" [ref=e207]
            - cell "Period Overtime" [ref=e208]
          - row [ref=e209]:
            - cell "Week 1 - Saturday" [ref=e210]
            - cell [ref=e211]:
              - generic [ref=e212]:
                - button "Decrease Saturday start time" [ref=e213]: −
                - textbox "Week 1 Saturday primary shift start" [ref=e214]
                - button "Increase Saturday start time" [ref=e215]: +
            - cell [ref=e216]:
              - generic [ref=e217]:
                - button "Decrease Saturday end time" [ref=e218]: −
                - textbox "Week 1 Saturday primary shift end" [ref=e219]
                - button "Increase Saturday end time" [ref=e220]: +
            - cell [ref=e221]:
              - generic [ref=e222]:
                - spinbutton "Week 1 Saturday primary unpaid break hours" [ref=e223]: "0.5"
                - generic [ref=e224]:
                  - button "Clear" [ref=e225]
                  - button "Copy Prev" [ref=e226]
                  - button "+ Add shift" [ref=e227]
            - cell [ref=e228]:
              - checkbox "Week 1 Saturday manual overtime" [ref=e229]
            - cell [ref=e230]:
              - checkbox "Week 1 Saturday manual ordinary" [ref=e231]
            - cell [ref=e232]:
              - checkbox "Week 1 Saturday public holiday" [ref=e233]
            - cell "0.00" [ref=e234]
            - cell "0.00" [ref=e235]
            - cell "0.00" [ref=e236]
            - cell "-" [ref=e237]
          - row [ref=e238]:
            - cell "Week 1 - Sunday" [ref=e239]
            - cell [ref=e240]:
              - generic [ref=e241]:
                - button "Decrease Sunday start time" [ref=e242]: −
                - textbox "Week 1 Sunday primary shift start" [ref=e243]
                - button "Increase Sunday start time" [ref=e244]: +
            - cell [ref=e245]:
              - generic [ref=e246]:
                - button "Decrease Sunday end time" [ref=e247]: −
                - textbox "Week 1 Sunday primary shift end" [ref=e248]
                - button "Increase Sunday end time" [ref=e249]: +
            - cell [ref=e250]:
              - generic [ref=e251]:
                - spinbutton "Week 1 Sunday primary unpaid break hours" [ref=e252]: "0.5"
                - generic [ref=e253]:
                  - button "Clear" [ref=e254]
                  - button "Copy Prev" [ref=e255]
                  - button "+ Add shift" [ref=e256]
            - cell [ref=e257]:
              - checkbox "Week 1 Sunday manual overtime" [ref=e258]
            - cell [ref=e259]:
              - checkbox "Week 1 Sunday manual ordinary" [ref=e260]
            - cell [ref=e261]:
              - checkbox "Week 1 Sunday public holiday" [ref=e262]
            - cell "0.00" [ref=e263]
            - cell "0.00" [ref=e264]
            - cell "0.00" [ref=e265]
            - cell "-" [ref=e266]
          - row [ref=e267]:
            - cell "Week 2 - Monday" [ref=e268]
            - cell [ref=e269]:
              - generic [ref=e270]:
                - button "Decrease Monday start time" [ref=e271]: −
                - textbox "Week 2 Monday primary shift start" [ref=e272]: "9"
                - button "Increase Monday start time" [ref=e273]: +
            - cell [ref=e274]:
              - generic [ref=e275]:
                - button "Decrease Monday end time" [ref=e276]: −
                - textbox "Week 2 Monday primary shift end" [ref=e277]: "17"
                - button "Increase Monday end time" [ref=e278]: +
            - cell [ref=e279]:
              - generic [ref=e280]:
                - spinbutton "Week 2 Monday primary unpaid break hours" [ref=e281]: "0"
                - generic [ref=e282]:
                  - button "Clear" [ref=e283]
                  - button "Copy Prev" [ref=e284]
                  - button "+ Add shift" [ref=e285]
            - cell [ref=e286]:
              - checkbox "Week 2 Monday manual overtime" [ref=e287]
            - cell [ref=e288]:
              - checkbox "Week 2 Monday manual ordinary" [ref=e289]
            - cell [ref=e290]:
              - checkbox "Week 2 Monday public holiday" [ref=e291]
            - cell "8.00" [ref=e292]
            - cell "8.00" [ref=e293]
            - cell "0.00" [ref=e294]
            - cell "-" [ref=e295]
          - row [ref=e296]:
            - cell "Week 2 - Tuesday" [ref=e297]
            - cell [ref=e298]:
              - generic [ref=e299]:
                - button "Decrease Tuesday start time" [ref=e300]: −
                - textbox "Week 2 Tuesday primary shift start" [ref=e301]: "9"
                - button "Increase Tuesday start time" [ref=e302]: +
            - cell [ref=e303]:
              - generic [ref=e304]:
                - button "Decrease Tuesday end time" [ref=e305]: −
                - textbox "Week 2 Tuesday primary shift end" [ref=e306]: "17"
                - button "Increase Tuesday end time" [ref=e307]: +
            - cell [ref=e308]:
              - generic [ref=e309]:
                - spinbutton "Week 2 Tuesday primary unpaid break hours" [ref=e310]: "0"
                - generic [ref=e311]:
                  - button "Clear" [ref=e312]
                  - button "Copy Prev" [ref=e313]
                  - button "+ Add shift" [ref=e314]
            - cell [ref=e315]:
              - checkbox "Week 2 Tuesday manual overtime" [ref=e316]
            - cell [ref=e317]:
              - checkbox "Week 2 Tuesday manual ordinary" [ref=e318]
            - cell [ref=e319]:
              - checkbox "Week 2 Tuesday public holiday" [ref=e320]
            - cell "8.00" [ref=e321]
            - cell "8.00" [ref=e322]
            - cell "0.00" [ref=e323]
            - cell "-" [ref=e324]
          - row [ref=e325]:
            - cell "Week 2 - Wednesday" [ref=e326]
            - cell [ref=e327]:
              - generic [ref=e328]:
                - button "Decrease Wednesday start time" [ref=e329]: −
                - textbox "Week 2 Wednesday primary shift start" [ref=e330]: "9"
                - button "Increase Wednesday start time" [ref=e331]: +
            - cell [ref=e332]:
              - generic [ref=e333]:
                - button "Decrease Wednesday end time" [ref=e334]: −
                - textbox "Week 2 Wednesday primary shift end" [ref=e335]: "17"
                - button "Increase Wednesday end time" [ref=e336]: +
            - cell [ref=e337]:
              - generic [ref=e338]:
                - spinbutton "Week 2 Wednesday primary unpaid break hours" [ref=e339]: "0"
                - generic [ref=e340]:
                  - button "Clear" [ref=e341]
                  - button "Copy Prev" [ref=e342]
                  - button "+ Add shift" [ref=e343]
            - cell [ref=e344]:
              - checkbox "Week 2 Wednesday manual overtime" [ref=e345]
            - cell [ref=e346]:
              - checkbox "Week 2 Wednesday manual ordinary" [ref=e347]
            - cell [ref=e348]:
              - checkbox "Week 2 Wednesday public holiday" [ref=e349]
            - cell "8.00" [ref=e350]
            - cell "8.00" [ref=e351]
            - cell "0.00" [ref=e352]
            - cell "-" [ref=e353]
          - row [ref=e354]:
            - cell "Week 2 - Thursday" [ref=e355]
            - cell [ref=e356]:
              - generic [ref=e357]:
                - button "Decrease Thursday start time" [ref=e358]: −
                - textbox "Week 2 Thursday primary shift start" [ref=e359]: "9"
                - button "Increase Thursday start time" [ref=e360]: +
            - cell [ref=e361]:
              - generic [ref=e362]:
                - button "Decrease Thursday end time" [ref=e363]: −
                - textbox "Week 2 Thursday primary shift end" [ref=e364]: "17"
                - button "Increase Thursday end time" [ref=e365]: +
            - cell [ref=e366]:
              - generic [ref=e367]:
                - spinbutton "Week 2 Thursday primary unpaid break hours" [ref=e368]: "0"
                - generic [ref=e369]:
                  - button "Clear" [ref=e370]
                  - button "Copy Prev" [ref=e371]
                  - button "+ Add shift" [ref=e372]
            - cell [ref=e373]:
              - checkbox "Week 2 Thursday manual overtime" [ref=e374]
            - cell [ref=e375]:
              - checkbox "Week 2 Thursday manual ordinary" [ref=e376]
            - cell [ref=e377]:
              - checkbox "Week 2 Thursday public holiday" [ref=e378]
            - cell "8.00" [ref=e379]
            - cell "8.00" [ref=e380]
            - cell "0.00" [ref=e381]
            - cell "-" [ref=e382]
          - row [ref=e383]:
            - cell "Week 2 - Friday" [ref=e384]
            - cell [ref=e385]:
              - generic [ref=e386]:
                - button "Decrease Friday start time" [ref=e387]: −
                - textbox "Week 2 Friday primary shift start" [ref=e388]: "9"
                - button "Increase Friday start time" [ref=e389]: +
            - cell [ref=e390]:
              - generic [ref=e391]:
                - button "Decrease Friday end time" [ref=e392]: −
                - textbox "Week 2 Friday primary shift end" [ref=e393]: "17"
                - button "Increase Friday end time" [ref=e394]: +
            - cell [ref=e395]:
              - generic [ref=e396]:
                - spinbutton "Week 2 Friday primary unpaid break hours" [active] [ref=e397]: "0"
                - generic [ref=e398]:
                  - button "Clear" [ref=e399]
                  - button "Copy Prev" [ref=e400]
                  - button "+ Add shift" [ref=e401]
            - cell [ref=e402]:
              - checkbox "Week 2 Friday manual overtime" [ref=e403]
            - cell [ref=e404]:
              - checkbox "Week 2 Friday manual ordinary" [ref=e405]
            - cell [ref=e406]:
              - checkbox "Week 2 Friday public holiday" [ref=e407]
            - cell "8.00" [ref=e408]
            - cell "6.00" [ref=e409]
            - cell "2.00" [ref=e410]
            - cell "Period Overtime" [ref=e411]
          - row [ref=e412]:
            - cell "Week 2 - Saturday" [ref=e413]
            - cell [ref=e414]:
              - generic [ref=e415]:
                - button "Decrease Saturday start time" [ref=e416]: −
                - textbox "Week 2 Saturday primary shift start" [ref=e417]
                - button "Increase Saturday start time" [ref=e418]: +
            - cell [ref=e419]:
              - generic [ref=e420]:
                - button "Decrease Saturday end time" [ref=e421]: −
                - textbox "Week 2 Saturday primary shift end" [ref=e422]
                - button "Increase Saturday end time" [ref=e423]: +
            - cell [ref=e424]:
              - generic [ref=e425]:
                - spinbutton "Week 2 Saturday primary unpaid break hours" [ref=e426]: "0.5"
                - generic [ref=e427]:
                  - button "Clear" [ref=e428]
                  - button "Copy Prev" [ref=e429]
                  - button "+ Add shift" [ref=e430]
            - cell [ref=e431]:
              - checkbox "Week 2 Saturday manual overtime" [ref=e432]
            - cell [ref=e433]:
              - checkbox "Week 2 Saturday manual ordinary" [ref=e434]
            - cell [ref=e435]:
              - checkbox "Week 2 Saturday public holiday" [ref=e436]
            - cell "0.00" [ref=e437]
            - cell "0.00" [ref=e438]
            - cell "0.00" [ref=e439]
            - cell "-" [ref=e440]
          - row [ref=e441]:
            - cell "Week 2 - Sunday" [ref=e442]
            - cell [ref=e443]:
              - generic [ref=e444]:
                - button "Decrease Sunday start time" [ref=e445]: −
                - textbox "Week 2 Sunday primary shift start" [ref=e446]
                - button "Increase Sunday start time" [ref=e447]: +
            - cell [ref=e448]:
              - generic [ref=e449]:
                - button "Decrease Sunday end time" [ref=e450]: −
                - textbox "Week 2 Sunday primary shift end" [ref=e451]
                - button "Increase Sunday end time" [ref=e452]: +
            - cell [ref=e453]:
              - generic [ref=e454]:
                - spinbutton "Week 2 Sunday primary unpaid break hours" [ref=e455]: "0.5"
                - generic [ref=e456]:
                  - button "Clear" [ref=e457]
                  - button "Copy Prev" [ref=e458]
                  - button "+ Add shift" [ref=e459]
            - cell [ref=e460]:
              - checkbox "Week 2 Sunday manual overtime" [ref=e461]
            - cell [ref=e462]:
              - checkbox "Week 2 Sunday manual ordinary" [ref=e463]
            - cell [ref=e464]:
              - checkbox "Week 2 Sunday public holiday" [ref=e465]
            - cell "0.00" [ref=e466]
            - cell "0.00" [ref=e467]
            - cell "0.00" [ref=e468]
            - cell "-" [ref=e469]
          - row [ref=e470]:
            - cell "Totals" [ref=e471]
            - cell [ref=e472]
            - cell [ref=e473]
            - cell [ref=e474]
            - cell "80.00" [ref=e475]
            - cell "76.00" [ref=e476]
            - cell "4.00" [ref=e477]
            - cell [ref=e478]
    - region [ref=e479]:
      - generic [ref=e480]:
        - paragraph [ref=e481]: Calculated from your shifts
        - heading "Pay breakdown" [level=2] [ref=e482]
        - generic [ref=e483]:
          - paragraph [ref=e484]: Gross pay
          - generic [ref=e485]: $2,460.00
          - paragraph [ref=e486]: Before tax and other deductions
        - generic [ref=e487]:
          - generic [ref=e488]:
            - generic [ref=e489]: Ordinary
            - generic [ref=e490]: $2,280.00
            - generic [ref=e491]: 76.00 hrs
          - generic [ref=e492]:
            - generic [ref=e493]: Overtime
            - generic [ref=e494]: $180.00
            - generic [ref=e495]: 4.00 hrs
          - generic [ref=e496]:
            - generic [ref=e497]: Penalty
            - generic [ref=e498]: $0.00
            - generic [ref=e499]: Applies to eligible hours
          - generic [ref=e500]:
            - generic [ref=e501]: Top-up
            - generic [ref=e502]: $0.00
            - generic [ref=e503]: 0.00 hrs
      - generic [ref=e504]:
        - paragraph [ref=e505]: Estimated take-home
        - generic [ref=e506]: $2,037.42
        - generic [ref=e507]: Includes estimated income tax and the 2% Medicare levy only.
```

# Test source

```ts
  1   | import { expect, test } from '@playwright/test';
  2   | import { RATE, hospitalityShiftWorker, partTimeTopUp } from './payroll-reference.js';
  3   | 
  4   | const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  5   | 
  6   | function inputName(shift, field) {
  7   |   return `Week ${shift.week ?? 1} ${shift.day} ${shift.additional ? 'additional' : 'primary'} shift ${field}`;
  8   | }
  9   | 
  10  | async function openCalculator(page, { employment = 'casual' } = {}) {
  11  |   await page.goto('/');
  12  |   await expect(page.getByRole('heading', { name: 'Pay breakdown' })).toBeVisible();
  13  |   await page.getByLabel('Hourly Rate ($)').fill(String(RATE));
  14  |   if (employment === 'casual') await page.getByRole('button', { name: 'Casual' }).click();
  15  |   for (const week of [1, 2]) {
  16  |     for (const day of weekdays) {
  17  |       await page.getByRole('row', { name: new RegExp(`Week ${week} - ${day}`) }).getByTitle('Clear times').click();
  18  |     }
  19  |   }
  20  | }
  21  | 
  22  | async function enterShifts(page, shifts) {
  23  |   for (const shift of shifts) {
  24  |     if (shift.additional) {
  25  |       await page.getByRole('row', { name: new RegExp(`Week ${shift.week ?? 1} - ${shift.day}`) }).getByTitle('Add another shift period').click();
  26  |     }
  27  |     await page.getByLabel(inputName(shift, 'start')).fill(String(shift.start));
  28  |     await page.getByLabel(inputName(shift, 'end')).fill(String(shift.end));
  29  |     await page.getByLabel(`Week ${shift.week ?? 1} ${shift.day} ${shift.additional ? 'additional' : 'primary'} unpaid break hours`).fill(String(shift.break ?? 0));
  30  |   }
  31  | }
  32  | 
  33  | function money(value) {
  34  |   return new Intl.NumberFormat('en-AU', {
  35  |     style: 'currency', currency: 'AUD', minimumFractionDigits: 2,
  36  |   }).format(value);
  37  | }
  38  | 
  39  | async function expectSummary(page, expected, context) {
  40  |   await expect(page.getByTestId('gross-pay'), context).toHaveText(money(expected.gross));
  41  |   await expect(page.getByTestId('ordinary-summary'), context).toContainText(`${expected.ordinary.toFixed(2)} hrs`);
  42  |   await expect(page.getByTestId('overtime-summary'), context).toContainText(`${expected.overtime.toFixed(2)} hrs`);
  43  |   if ('penaltyPay' in expected) await expect(page.getByTestId('penalty-summary'), context).toContainText(money(expected.penaltyPay));
  44  | }
  45  | 
  46  | const matrix = [
  47  |   {
  48  |     name: 'ordinary weekday 9–5 roster with unpaid lunches',
  49  |     shifts: weekdays.slice(0, 5).map((day) => ({ day, start: 9, end: 17, break: .5 })),
  50  |     applied: [],
  51  |   },
  52  |   {
  53  |     name: 'short shift plus a long shift above daily overtime',
  54  |     shifts: [{ day: 'Monday', start: 9, end: 12, break: .5 }, { day: 'Tuesday', start: 8, end: 19, break: .5 }],
  55  |     applied: ['Daily Overtime'],
  56  |   },
  57  |   {
  58  |     name: 'ten shifts that exceed the fortnightly ordinary limit',
  59  |     shifts: [1, 2].flatMap((week) => weekdays.slice(0, 5).map((day) => ({ week, day, start: 9, end: 17, break: 0 }))),
  60  |     applied: ['Period Overtime'],
  61  |   },
  62  |   {
  63  |     name: 'hospitality evening, Saturday and Sunday roster',
  64  |     shifts: [{ day: 'Friday', start: 18, end: 22, break: 0 }, { day: 'Saturday', start: 9, end: 17, break: 0 }, { day: 'Sunday', start: 9, end: 17, break: 0 }],
  65  |     applied: ['Evening Hours Penalty (20%)', 'Saturday Penalty (25%)', 'Sunday Penalty (50%)'],
  66  |   },
  67  |   {
  68  |     name: 'split hospitality shift with evening loading only on attended time',
  69  |     shifts: [{ day: 'Monday', start: 9, end: 12, break: 0 }, { day: 'Monday', additional: true, start: 17, end: 22, break: 0 }],
  70  |     applied: ['Evening Hours Penalty (20%)'],
  71  |   },
  72  | ];
  73  | 
  74  | for (const scenario of matrix) {
  75  |   test(`payroll math: ${scenario.name}`, async ({ page }) => {
  76  |     await openCalculator(page);
  77  |     await enterShifts(page, scenario.shifts);
  78  |     const expected = hospitalityShiftWorker(scenario.shifts);
  79  |     const context = `\nshifts=${JSON.stringify(scenario.shifts)}\nexpected=${JSON.stringify(expected)}`;
  80  |     await expectSummary(page, expected, context);
> 81  |     for (const rule of scenario.applied) await expect(page.getByText(rule, { exact: false }), context).toBeVisible();
      |                                                                                                        ^ Error: 
  82  |   });
  83  | }
  84  | 
  85  | test('part-time contracted-hours top-up changes exactly when a shift is amended', async ({ page }) => {
  86  |   await openCalculator(page, { employment: 'full_time' });
  87  |   await page.getByRole('button', { name: 'Part Time' }).click();
  88  |   await page.getByLabel('Effective Contracted Hours per Week').fill('20');
  89  |   const shifts = [{ day: 'Monday', start: 9, end: 17, break: 0 }, { day: 'Tuesday', start: 9, end: 17, break: 0 }];
  90  |   await enterShifts(page, shifts);
  91  |   const initial = partTimeTopUp(16, 20);
  92  |   await expect(page.getByTestId('topup-summary')).toContainText(`${initial.topup.toFixed(2)} hrs`);
  93  |   await expect(page.getByTestId('gross-pay')).toHaveText(money(initial.gross));
  94  |   await page.getByLabel(inputName(shifts[1], 'end')).fill('19');
  95  |   const amended = partTimeTopUp(18, 20);
  96  |   await expect(page.getByTestId('topup-summary')).toContainText(`${amended.topup.toFixed(2)} hrs`);
  97  |   await expect(page.getByTestId('gross-pay')).toHaveText(money(amended.gross));
  98  |   await expect(page.getByText('Contracted Hours Top-up', { exact: false })).toBeVisible();
  99  | });
  100 | 
  101 | test('full-time top-up entitlement is disabled and re-enabled through a custom ruleset', async ({ page }) => {
  102 |   await openCalculator(page, { employment: 'full_time' });
  103 |   await page.getByRole('button', { name: 'Edit rule configuration' }).click();
  104 |   await page.getByLabel('New custom configuration name').fill('E2E full-time-topup-toggle');
  105 |   await page.getByLabel('Contracted-hours top-up for full-time employees').selectOption('false');
  106 |   await page.getByRole('button', { name: 'Save custom copy' }).click();
  107 |   await expect(page.getByLabel('Rule Configuration')).toHaveValue('custom:hospitality:e2e-full-time-topup-toggle');
  108 | 
  109 |   const shift = { day: 'Monday', start: 9, end: 17, break: 0 };
  110 |   await enterShifts(page, [shift]);
  111 |   await expect(page.getByTestId('topup-summary')).toContainText('0.00 hrs');
  112 |   await expect(page.getByTestId('gross-pay')).toHaveText(money(8 * RATE));
  113 |   await expect(page.getByText('Contracted Hours Top-up', { exact: true })).toHaveCount(0);
  114 | 
  115 |   await page.getByRole('button', { name: 'Close rule editor' }).click();
  116 |   await page.getByRole('button', { name: 'Edit rule configuration' }).click();
  117 |   await page.getByLabel('Contracted-hours top-up for full-time employees').selectOption('true');
  118 |   await page.getByRole('button', { name: 'Save changes' }).click();
  119 |   const enabled = partTimeTopUp(8, 38);
  120 |   await expect(page.getByTestId('topup-summary')).toContainText(`${enabled.topup.toFixed(2)} hrs`);
  121 |   await expect(page.getByTestId('gross-pay')).toHaveText(money(enabled.gross));
  122 |   await expect(page.getByText('Contracted Hours Top-up', { exact: true })).toBeVisible();
  123 | });
  124 | 
  125 | test('custom award mutation changes daily overtime threshold through the frontend', async ({ page }) => {
  126 |   await openCalculator(page);
  127 |   await page.getByRole('button', { name: 'Edit rule configuration' }).click();
  128 |   await page.getByLabel('New custom configuration name').fill('E2E daily-overtime-8');
  129 |   await page.getByLabel('Daily ordinary-hours limit Shift workers').fill('8');
  130 |   await page.getByRole('button', { name: 'Save custom copy' }).click();
  131 |   await expect(page.getByLabel('Rule Configuration')).toContainText('Custom: E2E Daily Overtime 8');
  132 |   const shift = { day: 'Monday', start: 8, end: 17, break: 0 };
  133 |   await enterShifts(page, [shift]);
  134 |   await expectSummary(page, hospitalityShiftWorker([shift], { dailyLimit: 8 }), 'daily limit 8');
  135 |   await expect(page.getByRole('cell', { name: 'Daily Overtime', exact: true })).toBeVisible();
  136 | 
  137 |   await page.getByRole('button', { name: 'Close rule editor' }).click();
  138 |   await page.getByRole('button', { name: 'Edit rule configuration' }).click();
  139 |   await page.getByLabel('Daily ordinary-hours limit Shift workers').fill('10');
  140 |   await page.getByRole('button', { name: 'Save changes' }).click();
  141 |   await expect(page.getByLabel('Rule Configuration')).toContainText('Custom: E2E Daily Overtime 8');
  142 |   await expectSummary(page, hospitalityShiftWorker([shift], { dailyLimit: 10 }), 'daily limit 10');
  143 | });
  144 | 
  145 | test('invalid overlapping periods are rejected rather than silently paid', async ({ page }) => {
  146 |   await openCalculator(page);
  147 |   const first = { day: 'Monday', start: 9, end: 14, break: 0 };
  148 |   const second = { day: 'Monday', additional: true, start: 13, end: 17, break: 0 };
  149 |   await enterShifts(page, [first, second]);
  150 |   await expect(page.getByRole('alert')).toContainText('Overlapping shifts are not allowed');
  151 | });
  152 | 
```