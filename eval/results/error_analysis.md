# Error Analysis Report

## Summary

| Category | Count |
|---|---:|
| retrieval_miss | 42 |
| generation_error | 1 |
| **Total** | **43** |

## Representative Failures

| Question | Category | Reason | Suggested Fix |
|---|---|---|---|
| באיזה מקום נאמר: "וַיָּבֹא הָעָם ... וַיֵּשְׁבוּ שָׁם עַד הָעֶרֶב לִפְנֵי הָאֱלֹהִים וַיִּשְׂאוּ קוֹלָם וַיִּבְכּוּ בְּכִי גָדוֹל"? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| אַשְׁרֵי אֲנָשֶׁיךָ אַשְׁרֵי עֲבָדֶיךָ אֵלֶּה הָעֹמְדִים לְפָנֶיךָ תָּמִיד הַשֹּׁמְעִים אֶת־חָכְמָתֶךָ מי אמר למי את הדברים? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| כמה זמן היה ארון ה' בשדה פלישתים? | generation_error | Correct context was retrieved, but the LLM failed to extract the correct answer. | Refine the generation prompt or use a more capable LLM. |
| וְאִם־יֶשׁ־בִּי עָון וֶהֱמִתָנִי נאמר ל: | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| וּבְנֵי־יִשְׂרָאֵל עָשׂוּ כַּאֲשֶׁר צִוָּה ה' אֶת־מֹשֶׁה. מהו הציווי אותו עשו בני ישראל? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| וַתִּקַּח ... צֹר וַתִּכְרֹת אֶת עָרְלַת בְּנָהּ וַתַּגַּע לְרַגְלָיו וַתֹּאמֶר כִּי חֲתַן דָּמִים אַתָּה לִי על מי נאמר? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| למי נאמר: "לֹא יָמוּשׁ סֵפֶר הַתּוֹרָה הַזֶּה מִפִּיךָ וְהָגִיתָ בּוֹ יוֹמָם וָלַיְלָה לְמַעַן תִּשְׁמֹר לַעֲשׂוֹת כְּכׇל הַכָּתוּב בּוֹ כִּי אָז תַּצְלִיחַ אֶת דְּרָכֶךָ וְאָז תַּשְׂכִּיל"? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| מי אמר למי: "הַמְצָאתַנִי אֹיְבִי"? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| על מי נאמר: "וְיִקְרְאוּ אֶל־אֱלֹהִים בְּחָזְקָה"? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| "חֹבֵט חִטִּים בַּגַּת לְהָנִיס מִפְּנֵי מִדְיָן". מיהו חובט החטים? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| מהו גבול האמורי? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| מי אמר למי: "בֵּיתְךָ נִשְׂרֹף עָלֶיךָ בָּאֵשׁ"? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| אחרי איזה קרב נאמר:"וַיִּמַּס לְבַב הָעָם וַיְהִי לְמָיִם"? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| למי נאמר: "לֵךְ וְאַרְאֶךָּ אֶת הָאִישׁ אֲשֶׁר אַתָּה מְבַקֵּשׁ"? | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
| אֲשֶׁר לֹא־הָיָה כָמֹהוּ בְּכָל־אֶרֶץ מִצְרַיִם, מֵאָז הָיְתָה לְגוֹי נאמר על: | retrieval_miss | No relevant chunks were found in the top retrieved results. | Improve embedding model or add lexical/keyword boost. |
