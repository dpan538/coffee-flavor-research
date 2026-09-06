import copy
import unittest
import source_native_supervision_r5 as native


def row(i, x=5, y=5):
    return {
        "observation_id": str(i),
        "conservative_split_group": str(i),
        "process": "natural",
        "native_concentration_wv": 0.07,
        "minimum_auxiliary_view": {
            "A": [],
            "B": {"native.Flavour": x},
            "T": {"native.Bitterness": y},
        },
        "Score": 99,
    }


class NativeResponseTests(unittest.TestCase):
    def test_inference_does_not_require_or_read_target(self):
        rows = [row(i, i, 10 - i) for i in range(8)]
        model = native.fit(rows, True)
        request = copy.deepcopy(rows[0])
        del request["minimum_auxiliary_view"]["T"]
        self.assertEqual(native.predict(request, model), native.predict(rows[0], model))

    def test_quality_and_identity_do_not_change_prediction(self):
        rows = [row(i, i, 10 - i) for i in range(8)]
        model = native.fit(rows, True)
        changed = copy.deepcopy(rows[0])
        changed.update(Score=-999, process="different", observation_id="not-feature")
        self.assertEqual(native.predict(changed, model), native.predict(rows[0], model))

    def test_actually_fits_single_native_attribute(self):
        rows = [row(i, i, 10 - i) for i in range(8)]
        mean, measured = native.fit(rows, False), native.fit(rows, True)
        self.assertLess(
            native.summary(native.evaluate(rows, measured))["MSE_native_units_squared"],
            native.summary(native.evaluate(rows, mean))["MSE_native_units_squared"],
        )

    def test_mismatch_keeps_T_and_group_blocks(self):
        rows = [row(i, i, 10 - i) for i in range(4)]
        wrong, count = native.wrong_B(rows)
        self.assertEqual(count, 4)
        for value in wrong:
            self.assertEqual(
                native.values(value)[1],
                native.values(rows[int(value["observation_id"])])[1],
            )

    def test_capacity_same_for_mean_and_observed(self):
        rows = [row(i, i, i) for i in range(4)]
        self.assertEqual(
            len(native.fit(rows, False)["coefficients"]),
            len(native.fit(rows, True)["coefficients"]),
        )


if __name__ == "__main__":
    unittest.main()
