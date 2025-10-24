

class CorrectionFactors:
    """
    A class to store correction factors for different parameters.
    """

    def __init__(self, solar=0.0, rain=0.0, temperature=0.0):
        self.factors = {
            "solar": solar,
            "rain": rain,
            "temperature": temperature,
        }

    def set_factor(self, parameter, value):
        """
        Set the correction factor for a specific parameter.
        """
        if parameter in self.factors:
            self.factors[parameter] = value
        else:
            raise ValueError(f"Unknown parameter: {parameter}")

    def get_factor(self, parameter):
        """
        Get the correction factor for a specific parameter.
        """
        return self.factors.get(parameter)