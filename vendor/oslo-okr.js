/*!
MIT License

Copyright © 2020 Oslo kommune

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Source: oslokommune/okr-tracker @ 06d87896644280771549c8c1c9212c11ea1f665f
Ported: src/util/keyResultProgress.js; src/util/kpiHelpers.js (deduplication only).
Changes: isolated UMD module; Intl formatting replaces d3 locale; original arithmetic retained.
Kaika validation, ordering and date adapters are original code in okr_modules.js.
*/
(function(root){
const formatValue = value => new Intl.NumberFormat("en", {maximumFractionDigits:2}).format(value);
const getPercentageCompleted = (current, target) => {
  if (target === 0) {
    return 0;
  }
  // Round with max 2 decimal (as with string formatted percentages)
  const percent = (current / target) * 100;
  const rounded = parseFloat(percent.toFixed(2));
  return rounded;
};

const getKeyResultProgressDetails = (keyResult) => {
  const { startValue, targetValue, currentValue: keyResultCurrentValue } = keyResult;
  const currentValue =
    keyResultCurrentValue === undefined ? startValue : keyResultCurrentValue;

  let totalNumberOfTasks;
  let totalCompletedTasks;
  let totalRemainingTasks;
  let percentageCompleted;

  if (startValue < targetValue) {
    const totalNumberOfTasksForPeriod = targetValue - startValue;
    const totalCompletedTasksForPeriod = currentValue - startValue;

    totalNumberOfTasks = targetValue;
    totalCompletedTasks = currentValue;
    totalRemainingTasks = totalNumberOfTasks - totalCompletedTasks;
    percentageCompleted = getPercentageCompleted(
      totalCompletedTasksForPeriod,
      totalNumberOfTasksForPeriod
    );
  } else {
    totalNumberOfTasks = startValue - targetValue;
    totalCompletedTasks = startValue - currentValue;
    totalRemainingTasks = totalNumberOfTasks - totalCompletedTasks;
    percentageCompleted = getPercentageCompleted(totalCompletedTasks, totalNumberOfTasks);
  }

  return {
    percentageCompleted,
    totalCompletedTasks,
    totalRemainingTasks: totalRemainingTasks >= 0 ? totalRemainingTasks : 0,
    totalNumberOfTasks,
    formattedTotalCompletedTasks: formatValue(totalCompletedTasks),
    formattedTotalRemainingTasks: formatValue(totalRemainingTasks),
    formattedTotalNumberOfTasks: formatValue(totalNumberOfTasks),
    isCompleted: percentageCompleted >= 100,
  };
};

function filterDuplicatedProgressValues(progressCollection) {
  const seenDates = [];

  return progressCollection.filter((a) => {
    const date = a.timestamp.toDate().toISOString().slice(0, 10);
    if (!seenDates.includes(date)) {
      seenDates.push(date);
      return true;
    }
    return false;
  });
}


const api = {getKeyResultProgressDetails,filterDuplicatedProgressValues};
if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.OsloOKR=api;
})(globalThis);
